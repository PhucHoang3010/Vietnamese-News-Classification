import csv
from collections import Counter, defaultdict


CSV_FILE = "uncertainty_report.csv"


def main():
    rows = []

    with open(
        CSV_FILE,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        reader = csv.DictReader(f)

        required = {
            "id",
            "title",
            "prediction",
            "margin",
            "human_category",
        }

        missing = required - set(reader.fieldnames or [])

        if missing:
            print("ERROR: Missing columns:")
            for col in missing:
                print(" -", col)
            return

        for row in reader:
            human = row["human_category"].strip()

            if not human:
                print(
                    f"ERROR: ID {row['id']} "
                    "has empty human_category"
                )
                return

            rows.append(row)

    print("=" * 80)
    print("P2 MODEL EVALUATION - HUMAN GROUND TRUTH")
    print("=" * 80)

    total = len(rows)

    # ------------------------------------------------------------
    # 1. Accuracy
    # ------------------------------------------------------------

    correct = sum(
        row["prediction"].strip()
        == row["human_category"].strip()
        for row in rows
    )

    accuracy = correct / total if total else 0

    print()
    print("1. OVERALL")
    print("-" * 80)
    print(f"Total   : {total}")
    print(f"Correct : {correct}")
    print(f"Wrong   : {total - correct}")
    print(f"Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    # ------------------------------------------------------------
    # 2. Per-class statistics
    # ------------------------------------------------------------

    classes = sorted(
        set(
            row["human_category"].strip()
            for row in rows
        )
    )

    true_count = Counter()
    pred_count = Counter()
    correct_count = Counter()

    for row in rows:
        true_label = row["human_category"].strip()
        pred_label = row["prediction"].strip()

        true_count[true_label] += 1
        pred_count[pred_label] += 1

        if true_label == pred_label:
            correct_count[true_label] += 1

    print()
    print("2. PER-CLASS RESULTS")
    print("-" * 80)

    print(
        f"{'Category':<20}"
        f"{'True':>8}"
        f"{'Pred':>8}"
        f"{'Correct':>10}"
        f"{'Recall':>10}"
    )

    for label in classes:
        true_n = true_count[label]
        pred_n = pred_count[label]
        correct_n = correct_count[label]

        recall = (
            correct_n / true_n
            if true_n
            else 0
        )

        print(
            f"{label:<20}"
            f"{true_n:>8}"
            f"{pred_n:>8}"
            f"{correct_n:>10}"
            f"{recall:>9.2%}"
        )

    # ------------------------------------------------------------
    # 3. Precision / Recall / F1
    # ------------------------------------------------------------

    precision_values = []
    recall_values = []
    f1_values = []

    for label in classes:
        tp = correct_count[label]
        fp = pred_count[label] - tp
        fn = true_count[label] - tp

        precision = (
            tp / (tp + fp)
            if (tp + fp)
            else 0
        )

        recall = (
            tp / (tp + fn)
            if (tp + fn)
            else 0
        )

        f1 = (
            2 * precision * recall
            / (precision + recall)
            if (precision + recall)
            else 0
        )

        precision_values.append(precision)
        recall_values.append(recall)
        f1_values.append(f1)

    macro_precision = (
        sum(precision_values) / len(precision_values)
        if precision_values
        else 0
    )

    macro_recall = (
        sum(recall_values) / len(recall_values)
        if recall_values
        else 0
    )

    macro_f1 = (
        sum(f1_values) / len(f1_values)
        if f1_values
        else 0
    )

    print()
    print("3. MACRO METRICS")
    print("-" * 80)
    print(f"Precision: {macro_precision:.4f}")
    print(f"Recall   : {macro_recall:.4f}")
    print(f"F1-score : {macro_f1:.4f}")

    # ------------------------------------------------------------
    # 4. Confusion Matrix
    # ------------------------------------------------------------

    matrix = defaultdict(Counter)

    for row in rows:
        true_label = row["human_category"].strip()
        pred_label = row["prediction"].strip()

        matrix[true_label][pred_label] += 1

    all_labels = sorted(
        set(classes)
        | set(pred_count.keys())
    )

    print()
    print("4. CONFUSION MATRIX")
    print("-" * 80)

    print(
        f"{'TRUE \\ PRED':<20}"
        + "".join(
            f"{label[:10]:>12}"
            for label in all_labels
        )
    )

    for true_label in all_labels:
        print(
            f"{true_label:<20}"
            + "".join(
                f"{matrix[true_label][pred]:>12}"
                for pred in all_labels
            )
        )

    # ------------------------------------------------------------
    # 5. Accuracy by margin
    # ------------------------------------------------------------

    bins = [
        ("<0.10", 0, 0.10),
        ("0.10-0.20", 0.10, 0.20),
        ("0.20-0.30", 0.20, 0.30),
        ("0.30-0.50", 0.30, 0.50),
        (">=0.50", 0.50, float("inf")),
    ]

    print()
    print("5. ACCURACY BY MARGIN")
    print("-" * 80)

    for name, low, high in bins:
        group = []

        for row in rows:
            margin = float(row["margin"])

            if low <= margin < high:
                group.append(row)

        if not group:
            continue

        group_correct = sum(
            r["prediction"].strip()
            == r["human_category"].strip()
            for r in group
        )

        group_accuracy = (
            group_correct / len(group)
        )

        print(
            f"{name:<12}"
            f"Count={len(group):>3}   "
            f"Correct={group_correct:>3}   "
            f"Wrong={len(group) - group_correct:>3}   "
            f"Accuracy={group_accuracy:.2%}"
        )

    # ------------------------------------------------------------
    # 6. Wrong predictions
    # ------------------------------------------------------------

    wrong = [
        row
        for row in rows
        if row["prediction"].strip()
        != row["human_category"].strip()
    ]

    print()
    print("6. WRONG PREDICTIONS")
    print("-" * 80)

    if not wrong:
        print("No wrong predictions.")
    else:
        for row in sorted(
            wrong,
            key=lambda r: float(r["margin"])
        ):
            print()
            print(f"ID       : {row['id']}")
            print(f"Title    : {row['title']}")
            print(f"Model    : {row['prediction']}")
            print(f"Human    : {row['human_category']}")
            print(f"Margin   : {float(row['margin']):.6f}")

    # ------------------------------------------------------------
    # 7. Threshold simulation
    # ------------------------------------------------------------

    print()
    print("7. UNKNOWN THRESHOLD SIMULATION")
    print("-" * 80)

    for threshold in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        uncertain = [
            row
            for row in rows
            if float(row["margin"]) < threshold
        ]

        confident = [
            row
            for row in rows
            if float(row["margin"]) >= threshold
        ]

        confident_correct = sum(
            row["prediction"].strip()
            == row["human_category"].strip()
            for row in confident
        )

        confident_accuracy = (
            confident_correct / len(confident)
            if confident
            else 0
        )

        wrong_hidden = sum(
            row["prediction"].strip()
            != row["human_category"].strip()
            for row in uncertain
        )

        print(
            f"threshold < {threshold:.2f} | "
            f"UNKNOWN={len(uncertain):>2} | "
            f"remaining={len(confident):>2} | "
            f"remaining_accuracy="
            f"{confident_accuracy:.2%} | "
            f"errors_caught={wrong_hidden}"
        )


if __name__ == "__main__":
    main()