from pathlib import Path

from datasets import load_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = PROJECT_ROOT / "data" / "external"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "viet_online_news_sample.csv"


def main():
    print("=" * 80)
    print("DOWNLOAD VIET ONLINE NEWS - SMALL SAMPLE")
    print("=" * 80)

    print("Loading dataset...")
    print("Only a small sample will be downloaded.")
    print()

    dataset = load_dataset(
        "VLUS06/VietOnlineNews",
        split="train",
    )

    print(f"Dataset loaded: {len(dataset):,} rows")
    print()
    print("Columns:")
    print(dataset.column_names)
    print()

    # Chỉ lấy tối đa 3000 bài.
    # Seed cố định để kết quả reproducible.
    sample_size = min(3000, len(dataset))

    dataset = dataset.shuffle(
        seed=42
    ).select(
        range(sample_size)
    )

    print(
        f"Saving sample: {len(dataset):,} rows"
    )

    dataset.to_csv(
        str(OUTPUT_FILE)
    )

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()