"""Dự đoán có bảo đảm (split conformal prediction) cho bộ phân loại tin tức.

Thay vì ép AI chọn đúng 1 chuyên mục, AI nêu một TẬP chuyên mục sao cho đáp án đúng nằm trong tập với xác suất >= 1 - alpha
(tính trung bình trên các bài mới cùng phân phối với tập hiệu chỉnh). Bài dễ -> tập 1 chuyên mục; bài mơ hồ -> 2-3 chuyên mục.

Cách làm (không cần xác suất, không cần huấn luyện lại):
  - điểm "lệch chuẩn" của một bài với đáp án y:  s(x, y) = (điểm SVM cao nhất) - (điểm SVM của y)  >= 0
  - hiệu chỉnh trên các bài AI CHƯA TỪNG THẤY (kiểm định + dự đoán chéo của bài huấn luyện, 4.675 bài):
      q = phân vị ceil((n+1)(1-alpha))/n của s(x, y_đúng), tính riêng cho từng chuyên mục (Mondrian)
  - tập dự đoán = { k : (điểm cao nhất) - (điểm của k) <= q_k }  -> luôn chứa chuyên mục điểm cao nhất
Độ phủ theo TỪNG chuyên mục >= 1 - alpha (Vovk 2003; Angelopoulos & Bates 2021), nên chuyên mục khó như Thời sự cũng được bảo đảm.
"""
import numpy as np

ALPHAS = (0.1, 0.05, 0.01)                     # bảo đảm 90% / 95% / 99%  (alpha = 0,05 là mức mặc định trên website)
METHOD = "margin-mondrian"                     # điểm lệch chuẩn theo khoảng cách điểm SVM, ngưỡng riêng cho từng chuyên mục


def margins(D):
    """(n, K): khoảng cách điểm SVM của từng chuyên mục so với điểm cao nhất (0 với chuyên mục đứng đầu)."""
    D = np.asarray(D, dtype=float)
    return D.max(axis=1, keepdims=True) - D


def conformal_quantile(scores, alpha):
    """Phân vị hữu hạn mẫu ceil((n+1)(1-alpha))/n; trả về +inf nếu quá ít mẫu (khi đó mọi chuyên mục đều được đưa vào tập)."""
    s = np.sort(np.asarray(scores, dtype=float))
    n = len(s)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    return float(s[k - 1]) if 1 <= k <= n else float("inf")


def calibrate(D, y_idx, alphas=ALPHAS):
    """Ngưỡng cho từng alpha: {'marginal': q chung, 'per_class': [q_0..q_K-1]}. D = điểm SVM tập hiệu chỉnh, y_idx = chỉ số đáp án đúng."""
    D = np.asarray(D, dtype=float); y_idx = np.asarray(y_idx)
    s = margins(D)[np.arange(len(D)), y_idx]
    K = D.shape[1]
    return {str(a): {"marginal": conformal_quantile(s, a), "per_class": [conformal_quantile(s[y_idx == k], a) for k in range(K)]} for a in alphas}


def predict_sets(D, thr, mondrian=True):
    """Mặt nạ bool (n, K): chuyên mục nào nằm trong tập dự đoán. Luôn chứa chuyên mục điểm cao nhất."""
    G = margins(D)
    q = np.asarray(thr["per_class"], dtype=float)[None, :] if mondrian else thr["marginal"]
    return G <= q


def evaluate(mask, y_idx):
    """Độ phủ, kích thước tập trung bình, tỉ lệ tập 1 chuyên mục và độ đúng của chúng, độ phủ thấp nhất theo chuyên mục."""
    mask = np.asarray(mask, dtype=bool); y_idx = np.asarray(y_idx)
    hit = mask[np.arange(len(mask)), y_idx]
    size = mask.sum(axis=1)
    one = size == 1
    K = mask.shape[1]
    per = [float(hit[y_idx == k].mean()) for k in range(K) if (y_idx == k).any()]
    return {"coverage": float(hit.mean()), "avg_size": float(size.mean()), "singleton_share": float(one.mean()),
            "singleton_acc": float(hit[one].mean()) if one.any() else float("nan"), "size_ge3_share": float((size >= 3).mean()),
            "worst_class_coverage": float(min(per)), "mean_class_coverage": float(np.mean(per))}


def cross_fit_scores(texts, labels, make_model, n_splits=5, seed=42):
    """Điểm SVM 'chưa từng thấy bài đó' cho mọi bài: mỗi fold huấn luyện trên các fold còn lại rồi chấm fold này (dự đoán chéo)."""
    from sklearn.model_selection import StratifiedKFold
    texts = np.asarray(texts, dtype=object); labels = np.asarray(labels)
    classes = sorted(set(labels.tolist()))
    D = np.zeros((len(texts), len(classes)))
    for tr, te in StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed).split(texts, labels):
        m = make_model().fit(texts[tr], labels[tr])
        assert list(m.classes_) == classes
        D[te] = m.decision_function(texts[te])
    return D
