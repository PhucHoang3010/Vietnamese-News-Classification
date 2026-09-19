from datasets import load_dataset


def main():
    print("=" * 80)
    print("INSPECT VIET ONLINE NEWS")
    print("=" * 80)

    print("Loading dataset...")
    print()

    dataset = load_dataset(
        "VLUS06/VietOnlineNews",
        split="train",
    )

    print(f"Total rows: {len(dataset):,}")
    print()
    print("Columns:")
    print(dataset.column_names)
    print()

    print("=" * 80)
    print("CATEGORY DISTRIBUTION")
    print("=" * 80)

    counts = {}

    for category in dataset["category"]:
        counts[category] = counts.get(category, 0) + 1

    for category, count in sorted(
        counts.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        percentage = count / len(dataset) * 100

        print(
            f"{str(category):<30}"
            f"{count:>10,}"
            f"  {percentage:>6.2f}%"
        )


if __name__ == "__main__":
    main()