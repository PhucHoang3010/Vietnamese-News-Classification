import asyncio
import csv
import os

import asyncpg
import joblib
from underthesea import word_tokenize


def margin_bin(margin):
    if margin < 0.10:
        return "<0.10"
    elif margin < 0.20:
        return "0.10–0.20"
    elif margin < 0.30:
        return "0.20–0.30"
    elif margin < 0.50:
        return "0.30–0.50"
    else:
        return ">=0.50"


async def main():
    print("=" * 80)
    print("VIETNAMESE NEWS - UNCERTAINTY SCAN")
    print("=" * 80)

    # Load model
    vectorizer = joblib.load(
        "/app/models/p2_tfidf_vectorizer.joblib"
    )
    model = joblib.load(
        "/app/models/p2_linear_svm_balanced.joblib"
    )

    print(f"Model: {type(model).__name__}")
    print(f"Classes: {len(model.classes_)}")

    # Connect PostgreSQL
    database_url = os.environ["DATABASE_URL"].replace(
        "postgresql+asyncpg://",
        "postgresql://",
        1,
    )

    conn = await asyncpg.connect(database_url)

    try:
        rows = await conn.fetch("""
            SELECT
                id,
                title,
                content,
                category,
                decision_score
            FROM news
            ORDER BY id
        """)

        print(f"Articles found: {len(rows)}")
        print()

        results = []

        for row in rows:
            article_id = row["id"]
            title = row["title"]
            content = row["content"]
            db_category = row["category"]
            db_score = float(row["decision_score"])

            # Same input reconstruction used in previous check
            text = f"{title} {content}"

            processed_text = " ".join(
                word_tokenize(text)
            )

            X = vectorizer.transform(
                [processed_text]
            )

            if X.nnz == 0:
                results.append({
                    "id": article_id,
                    "title": title,
                    "db_category": db_category,
                    "prediction": "UNKNOWN",
                    "db_score": db_score,
                    "top1_score": None,
                    "top2_score": None,
                    "margin": None,
                    "bin": "UNKNOWN",
                })
                continue

            prediction = model.predict(X)[0]

            scores = model.decision_function(X)[0]

            ranked = sorted(
                zip(model.classes_, scores),
                key=lambda x: x[1],
                reverse=True,
            )

            top1_label, top1_score = ranked[0]
            top2_label, top2_score = ranked[1]
            top3_label, top3_score = ranked[2]

            margin = float(top1_score - top2_score)

            results.append({
                "id": article_id,
                "title": title,
                "db_category": db_category,
                "prediction": prediction,
                "db_score": db_score,
                "top1_score": float(top1_score),
                "top2_score": float(top2_score),
                "margin": margin,
                "bin": margin_bin(margin),
            })

        # ------------------------------------------------------------------
        # 1. Prediction mismatch
        # ------------------------------------------------------------------

        mismatches = [
            r for r in results
            if r["prediction"] != r["db_category"]
        ]

        print("=" * 80)
        print("1. DB CATEGORY vs RECOMPUTED PREDICTION")
        print("=" * 80)

        print(f"Total articles : {len(results)}")
        print(f"Matches        : {len(results) - len(mismatches)}")
        print(f"Mismatches     : {len(mismatches)}")

        if mismatches:
            print("\nMISMATCHES:")
            for r in mismatches:
                print(
                    f"ID {r['id']:>3} | "
                    f"DB={r['db_category']:<15} | "
                    f"MODEL={r['prediction']:<15} | "
                    f"{r['title']}"
                )
        else:
            print("All stored categories match recomputed predictions.")

        # ------------------------------------------------------------------
        # 2. DB score consistency
        # ------------------------------------------------------------------

        score_mismatches = []

        for r in results:
            if r["top1_score"] is None:
                continue

            difference = abs(
                r["db_score"] - r["top1_score"]
            )

            if difference > 1e-6:
                score_mismatches.append(
                    (r, difference)
                )

        print()
        print("=" * 80)
        print("2. STORED decision_score vs RECOMPUTED TOP1 SCORE")
        print("=" * 80)

        print(
            f"Score mismatches (> 1e-6): "
            f"{len(score_mismatches)}"
        )

        if score_mismatches:
            print("\nFirst mismatches:")
            for r, diff in score_mismatches[:10]:
                print(
                    f"ID {r['id']:>3} | "
                    f"DB={r['db_score']:.6f} | "
                    f"NEW={r['top1_score']:.6f} | "
                    f"DIFF={diff:.6f}"
                )
        else:
            print("All stored scores match recomputed Top1 scores.")

        # ------------------------------------------------------------------
        # 3. Margin distribution
        # ------------------------------------------------------------------

        valid_results = [
            r for r in results
            if r["margin"] is not None
        ]

        bins = [
            "<0.10",
            "0.10–0.20",
            "0.20–0.30",
            "0.30–0.50",
            ">=0.50",
        ]

        counts = {
            b: 0
            for b in bins
        }

        for r in valid_results:
            counts[r["bin"]] += 1

        print()
        print("=" * 80)
        print("3. MARGIN DISTRIBUTION")
        print("=" * 80)

        for b in bins:
            count = counts[b]

            percentage = (
                count / len(valid_results) * 100
                if valid_results
                else 0
            )

            print(
                f"{b:<12} : "
                f"{count:>3} articles "
                f"({percentage:>6.2f}%)"
            )

        # ------------------------------------------------------------------
        # 4. Lowest margins
        # ------------------------------------------------------------------

        lowest_margin = sorted(
            valid_results,
            key=lambda r: r["margin"]
        )[:15]

        print()
        print("=" * 80)
        print("4. 15 MOST UNCERTAIN ARTICLES")
        print("=" * 80)

        for r in lowest_margin:
            print()
            print(
                f"ID      : {r['id']}"
            )
            print(
                f"Title   : {r['title']}"
            )
            print(
                f"Category: {r['prediction']}"
            )
            print(
                f"Top1    : {r['top1_score']:.6f}"
            )
            print(
                f"Top2    : {r['top2_score']:.6f}"
            )
            print(
                f"Margin  : {r['margin']:.6f}"
            )
            print(
                f"Bin     : {r['bin']}"
            )

        # ------------------------------------------------------------------
        # 5. Potential UNKNOWN candidates
        # ------------------------------------------------------------------

        thresholds = [0.10, 0.20, 0.30, 0.50]

        print()
        print("=" * 80)
        print("5. POTENTIAL UNKNOWN COUNTS")
        print("=" * 80)

        for threshold in thresholds:
            count = sum(
                1
                for r in valid_results
                if r["margin"] < threshold
            )

            percentage = (
                count / len(valid_results) * 100
                if valid_results
                else 0
            )

            print(
                f"margin < {threshold:.2f}: "
                f"{count} articles "
                f"({percentage:.2f}%)"
            )

        # ------------------------------------------------------------------
        # 6. CSV report
        # ------------------------------------------------------------------

        csv_path = "/app/uncertainty_report.csv"

        with open(
            csv_path,
            "w",
            newline="",
            encoding="utf-8-sig",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id",
                    "title",
                    "db_category",
                    "prediction",
                    "db_score",
                    "top1_score",
                    "top2_score",
                    "margin",
                    "bin",
                ],
            )

            writer.writeheader()
            writer.writerows(results)

        print()
        print("=" * 80)
        print(f"CSV report saved: {csv_path}")
        print("=" * 80)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())