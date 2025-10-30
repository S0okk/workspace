def generate_statistics(list_with_nums: list) -> dict:

    sorted_nums = sorted(list_with_nums)

    n = len(sorted_nums)

    if n % 2 != 0:
        median = sorted_nums[n // 2]
    else:
        median = (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2

    mean = sum(sorted_nums) / n
    standard_deviation = (sum((x - mean) ** 2 for x in sorted_nums) / n )** 0.5

    return {
        'mean': mean,
        'median': median,
        'standard_deviation': standard_deviation
    }

stats = generate_statistics([1, 2, 3, 4, 5])
print(stats)