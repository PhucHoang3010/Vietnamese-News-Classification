"""
generate_synthetic_data.py
==========================
PHASE 1 — Synthetic Data Generator

Mục đích:
- Sinh 300 mẫu synthetic tiếng Việt có cấu trúc giống tin tức
- 5 classes × 60 samples/class
- CHỈ DÙNG ĐỂ TEST PIPELINE PHASE 1
- KHÔNG PHẢI DATASET CHÍNH THỨC CỦA P2

Output:
- data/raw/news_raw.csv

Schema:
- id, title, content, label

Usage:
    python scripts/generate_synthetic_data.py
    python scripts/generate_synthetic_data.py --samples-per-class 100
    python scripts/generate_synthetic_data.py --output data/raw/custom.csv
"""

from __future__ import annotations

import argparse
import logging
import random
from pathlib import Path

import pandas as pd

# ============================================================
# CONFIG
# ============================================================

RANDOM_SEED = 42
SAMPLES_PER_CLASS = 60

CATEGORIES: dict[str, dict] = {
    "THỂ THAO": {
        "titles": [
            "Đội tuyển Việt Nam giành chiến thắng trong trận đấu mới",
            "CLB Hà Nội ký hợp đồng với tiền đạo ngoại",
            "VĐV điền kinh Việt Nam phá kỷ lục quốc gia",
            "Sea Games 32: Đoàn thể thao Việt Nam đặt mục tiêu cao",
            "HLV Park Hang-seo chia sẻ về chiến thuật mới",
            "Giải bóng đá V-League khởi tranh với nhiều bất ngờ",
            "Tay vợt Việt Nam lọt vào bán kết giải quốc tế",
            "Đội bóng nữ Việt Nam chuẩn bị cho vòng loại World Cup",
            "Kình ngư trẻ lập thành tích ấn tượng tại giải châu Á",
            "Đội tuyển U23 Việt Nam hội quân chuẩn bị giải mới",
            "Giải marathon quốc tế quy tụ hàng nghìn VĐV",
            "Võ sĩ Việt Nam bảo vệ thành công đai vô địch",
        ],
        "contents": [
            "Đội tuyển Việt Nam đã có màn trình diễn ấn tượng trong trận đấu tối qua. "
            "Các cầu thủ nhập cuộc đầy tự tin và tạo ra nhiều cơ hội nguy hiểm. "
            "HLV trưởng cho biết đội đang trong quá trình chuẩn bị cho giải đấu lớn sắp tới.",
            "Trong khuôn khổ giải đấu quốc tế, đại diện Việt Nam đã xuất sắc vượt qua đối thủ. "
            "Ban huấn luyện đánh giá cao tinh thần thi đấu của các vận động viên.",
            "Sự kiện thể thao thu hút sự quan tâm của đông đảo khán giả. "
            "Các chuyên gia nhận định đây là cơ hội để thể thao nước nhà khẳng định vị thế.",
            "Các vận động viên đã có buổi tập luyện nghiêm túc để chuẩn bị cho giải đấu. "
            "Ban tổ chức cho biết công tác chuẩn bị đang được triển khai đúng tiến độ.",
        ],
    },
    "KINH TẾ": {
        "titles": [
            "GDP Việt Nam tăng trưởng ấn tượng trong quý mới",
            "Xuất khẩu gạo đạt mức cao nhất trong nhiều năm",
            "Ngân hàng Nhà nước điều chỉnh lãi suất điều hành",
            "Vốn FDI vào Việt Nam tăng mạnh so với cùng kỳ",
            "Thị trường chứng khoán khởi sắc phiên đầu tuần",
            "Doanh nghiệp vừa và nhỏ được hỗ trợ vay vốn ưu đãi",
            "Lạm phát được kiểm soát trong biên độ an toàn",
            "Hiệp định thương mại mới mở ra cơ hội cho xuất khẩu",
            "Thu ngân sách nhà nước vượt kế hoạch đề ra",
            "Giá vàng trong nước biến động theo thị trường thế giới",
            "Nhiều doanh nghiệp niêm yết báo lãi lớn quý này",
            "Đầu tư công được đẩy mạnh trong những tháng cuối năm",
        ],
        "contents": [
            "Theo báo cáo mới nhất, tăng trưởng kinh tế có nhiều tín hiệu tích cực. "
            "Các ngành sản xuất và dịch vụ đóng góp chủ yếu vào mức tăng trưởng chung.",
            "Kim ngạch xuất khẩu ghi nhận mức tăng trưởng vượt kỳ vọng. "
            "Các mặt hàng chủ lực duy trì đà tăng ổn định.",
            "Thị trường tài chính ghi nhận nhiều diễn biến sôi động. "
            "Các nhà đầu tư nước ngoài tiếp tục quan tâm đến thị trường Việt Nam.",
            "Chính sách tiền tệ được điều hành linh hoạt để ổn định kinh tế vĩ mô. "
            "Các chuyên gia dự báo triển vọng khả quan cho giai đoạn tới.",
        ],
    },
    "GIẢI TRÍ": {
        "titles": [
            "Bộ phim Việt Nam gây sốt tại phòng vé",
            "Ca sĩ nổi tiếng ra mắt album mới sau nhiều năm",
            "Lễ trao giải âm nhạc thu hút đông đảo nghệ sĩ",
            "Chương trình truyền hình thực tế lập kỷ lục rating",
            "Diễn viên Việt Nam nhận giải thưởng quốc tế",
            "Nhóm nhạc trẻ khuấy động sân khấu với hit mới",
            "Liên hoan phim quốc tế quy tụ nhiều tác phẩm chất lượng",
            "Sự kiện ra mắt phim hoành tráng tại TP.HCM",
            "Gameshow mới lên sóng thu hút khán giả trẻ",
            "Nghệ sĩ Việt Nam biểu diễn tại sân khấu quốc tế",
            "Bộ phim truyền hình dài tập gây bão mạng xã hội",
            "Đêm nhạc hội tụ nhiều giọng ca hàng đầu",
        ],
        "contents": [
            "Tác phẩm mới nhận được nhiều lời khen từ giới phê bình và khán giả. "
            "Nội dung phim khai thác đề tài gần gũi với đời sống người Việt.",
            "Sự kiện giải trí thu hút sự tham gia của nhiều nghệ sĩ nổi tiếng. "
            "Chương trình được đầu tư kỹ lưỡng về nội dung và hình ảnh.",
            "Ngành công nghiệp giải trí Việt Nam đang có nhiều khởi sắc. "
            "Các sản phẩm mới liên tục được ra mắt và đón nhận tích cực.",
            "Khán giả có những trải nghiệm thú vị và cảm xúc khó quên. "
            "Sự kiện đánh dấu bước phát triển mới của làng giải trí nước nhà.",
        ],
    },
    "GIÁO DỤC": {
        "titles": [
            "Kỳ thi tốt nghiệp THPT có nhiều thay đổi quan trọng",
            "Bộ Giáo dục công bố chương trình mới cho năm học tới",
            "Trường đại học Việt Nam lọt top xếp hạng châu Á",
            "Học sinh Việt Nam giành giải cao tại Olympic quốc tế",
            "Đẩy mạnh chuyển đổi số trong giáo dục phổ thông",
            "Chính sách miễn giảm học phí cho sinh viên khó khăn",
            "Phương pháp dạy học mới được triển khai thí điểm",
            "Tuyển sinh đại học năm nay có nhiều điểm mới",
            "Nhiều trường học triển khai mô hình giáo dục STEM",
            "Học sinh Việt Nam đạt thành tích cao tại kỳ thi khu vực",
            "Bộ Giáo dục công bố đề thi tham khảo cho kỳ thi tới",
            "Nhiều trường đại học mở ngành đào tạo mới",
        ],
        "contents": [
            "Ngành giáo dục tiếp tục đổi mới để nâng cao chất lượng đào tạo. "
            "Các trường học chủ động thích ứng với chương trình mới.",
            "Học sinh Việt Nam thể hiện năng lực vượt trội tại các kỳ thi quốc tế. "
            "Thành tích này khẳng định chất lượng giáo dục của nước nhà.",
            "Chuyển đổi số trong giáo dục đang diễn ra mạnh mẽ. "
            "Các nền tảng học trực tuyến được sử dụng rộng rãi.",
            "Nhà trường và gia đình phối hợp để đảm bảo hiệu quả học tập. "
            "Nhiều chính sách hỗ trợ học sinh, sinh viên tiếp tục được triển khai.",
        ],
    },
    "PHÁP LUẬT": {
        "titles": [
            "Quốc hội thông qua luật mới về quản lý đất đai",
            "Tòa án nhân dân xét xử vụ án kinh tế lớn",
            "Bộ luật mới có hiệu lực từ đầu năm sau",
            "Cơ quan điều tra khởi tố vụ án tham nhũng",
            "Nhiều quy định mới về xử phạt giao thông",
            "Luật bảo vệ dữ liệu cá nhân được ban hành",
            "Tăng cường phòng chống tội phạm công nghệ cao",
            "Cải cách thủ tục hành chính trong lĩnh vực tư pháp",
            "Nhiều vụ việc vi phạm pháp luật bị xử lý nghiêm",
            "Quy định mới về quản lý hoạt động kinh doanh",
            "Tăng cường kiểm tra việc chấp hành pháp luật",
            "Nhiều chính sách pháp luật mới có hiệu lực",
        ],
        "contents": [
            "Các quy định pháp luật mới được ban hành nhằm hoàn thiện hệ thống pháp lý. "
            "Cơ quan chức năng tăng cường tuyên truyền, phổ biến pháp luật đến người dân.",
            "Phiên tòa xét xử thu hút sự quan tâm của dư luận. "
            "Hội đồng xét xử đã xem xét kỹ lưỡng các chứng cứ và lời khai.",
            "Công tác cải cách tư pháp được đẩy mạnh trong thời gian qua. "
            "Các thủ tục hành chính được đơn giản hóa, tạo thuận lợi cho người dân.",
            "Việc thực thi nghiêm minh góp phần ổn định trật tự xã hội. "
            "Nhiều vụ việc được xử lý đúng quy định của pháp luật.",
        ],
    },
}

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ============================================================
# GENERATOR
# ============================================================

def generate_sample(
    sample_id: int,
    category: str,
    title_pool: list[str],
    content_pool: list[str],
    rng: random.Random,
) -> dict:
    """Sinh một mẫu synthetic với variation."""
    title = rng.choice(title_pool)
    content = rng.choice(content_pool)

    variation_suffix = rng.choice([
        "",
        " Thông tin đang được cập nhật.",
        " Chi tiết sẽ được tiếp tục theo dõi.",
        " Đây là bản tin synthetic dùng cho mục đích kiểm thử pipeline.",
        " Nguồn tin đang được xác minh thêm.",
        " Phóng viên sẽ tiếp tục cập nhật diễn biến.",
    ])

    return {
        "id": f"synth-{sample_id:04d}",
        "title": title,
        "content": content + variation_suffix,
        "label": category,
    }


def generate_dataset(
    samples_per_class: int = SAMPLES_PER_CLASS,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """Sinh dataset synthetic hoàn chỉnh."""
    rng = random.Random(seed)
    rows: list[dict] = []
    counter = 1

    for category, pools in CATEGORIES.items():
        logger.info(f"Generating {samples_per_class} samples for '{category}'")
        for _ in range(samples_per_class):
            sample = generate_sample(
                sample_id=counter,
                category=category,
                title_pool=pools["titles"],
                content_pool=pools["contents"],
                rng=rng,
            )
            rows.append(sample)
            counter += 1

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    return df


# ============================================================
# MAIN
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Vietnamese news dataset for Phase 1 testing.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw/news_raw.csv"),
        help="Output CSV path (default: data/raw/news_raw.csv)",
    )
    parser.add_argument(
        "--samples-per-class",
        type=int,
        default=SAMPLES_PER_CLASS,
        help=f"Samples per class (default: {SAMPLES_PER_CLASS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help=f"Random seed (default: {RANDOM_SEED})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("SYNTHETIC DATA GENERATOR — PHASE 1")
    logger.info("=" * 60)
    logger.info(f"Output: {output_path}")
    logger.info(f"Classes: {list(CATEGORIES.keys())}")
    logger.info(f"Samples/class: {args.samples_per_class}")
    logger.info(f"Seed: {args.seed}")
    logger.info("-" * 60)

    df = generate_dataset(
        samples_per_class=args.samples_per_class,
        seed=args.seed,
    )

    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    logger.info("-" * 60)
    logger.info(f"✅ Total samples: {len(df)}")
    logger.info(f"✅ Classes: {df['label'].nunique()}")
    logger.info("Class distribution:")
    for label, count in df["label"].value_counts().sort_index().items():
        logger.info(f"   - {label}: {count}")
    logger.info(f"✅ Saved to: {output_path}")
    logger.info("=" * 60)
    logger.warning("⚠️  SYNTHETIC DATA — NOT FOR OFFICIAL ML TRAINING")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()