"""
Instrumented Sorting Algorithms & Synthetic Benchmark Data Generators
=====================================================================
Provides implementations of 4 classical sorting algorithms:
1. Bubble Sort (Unoptimized Quadratic Reference - O(N^2))
2. Quick Sort (Divide-and-Conquer In-Place - O(N log N) average)
3. Merge Sort (Stable Divide-and-Conquer - O(N log N))
4. Heap Sort (In-Place Binary Heap - O(N log N) worst-case)

Each algorithm tracks:
- Comparisons: Number of element-to-element comparisons
- Swaps / Moves: Number of element swaps or data assignments
- Total Operations: Sum of comparisons and memory moves
"""

import random
from typing import List, Tuple, Dict, Callable


def generate_dataset(size: int, distribution: str = "random", seed: int = None) -> List[int]:
    """
    Generates an integer array according to the specified distribution.
    
    Args:
        size: Number of elements.
        distribution: 'random', 'nearly_sorted', or 'reverse_sorted'.
        seed: Optional random seed for deterministic generation.
    
    Returns:
        List of integers.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    if distribution == "random":
        return [rng.randint(0, size * 10) for _ in range(size)]
    elif distribution == "nearly_sorted":
        arr = list(range(size))
        # Perturb roughly 5% of elements by swapping adjacent or nearby elements
        num_swaps = max(1, int(size * 0.05))
        for _ in range(num_swaps):
            i = rng.randint(0, size - 1)
            j = min(size - 1, max(0, i + rng.randint(-5, 5)))
            arr[i], arr[j] = arr[j], arr[i]
        return arr
    elif distribution == "reverse_sorted":
        return list(range(size, 0, -1))
    else:
        raise ValueError(f"Unknown distribution '{distribution}'. Choose from 'random', 'nearly_sorted', 'reverse_sorted'.")


def bubble_sort(arr: List[int]) -> Tuple[List[int], int, int, int]:
    """
    Standard Bubble Sort with operation counters.
    Time Complexity: O(N^2), Space Complexity: O(1).
    """
    a = list(arr)
    n = len(a)
    comparisons = 0
    swaps = 0

    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            comparisons += 1
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swaps += 1
                swapped = True
        if not swapped:
            break

    total_ops = comparisons + swaps
    return a, comparisons, swaps, total_ops


def quick_sort(arr: List[int]) -> Tuple[List[int], int, int, int]:
    """
    In-place Quick Sort using median-of-three pivot selection to prevent worst-case degradation.
    Time Complexity: O(N log N) average, Space Complexity: O(log N) stack.
    """
    a = list(arr)
    comparisons = 0
    swaps = 0

    def _quick_sort(low: int, high: int):
        nonlocal comparisons, swaps
        if low < high:
            # Median-of-three pivot selection
            mid = (low + high) // 2
            if a[mid] < a[low]:
                a[low], a[mid] = a[mid], a[low]
                swaps += 1
            comparisons += 1
            if a[high] < a[low]:
                a[low], a[high] = a[high], a[low]
                swaps += 1
            comparisons += 1
            if a[high] < a[mid]:
                a[mid], a[high] = a[high], a[mid]
                swaps += 1
            comparisons += 1

            # Place median pivot at high - 1
            a[mid], a[high - 1] = a[high - 1], a[mid]
            swaps += 1
            pivot = a[high - 1]

            i = low
            j = high - 1

            while True:
                i += 1
                while a[i] < pivot:
                    comparisons += 1
                    i += 1
                comparisons += 1

                j -= 1
                while a[j] > pivot:
                    comparisons += 1
                    j -= 1
                comparisons += 1

                if i >= j:
                    break
                a[i], a[j] = a[j], a[i]
                swaps += 1

            a[i], a[high - 1] = a[high - 1], a[i]
            swaps += 1

            _quick_sort(low, i - 1)
            _quick_sort(i + 1, high)

    if len(a) <= 1:
        return a, 0, 0, 0

    # Iterative fallback for small sub-arrays or simple recursive driver
    stack = [(0, len(a) - 1)]
    while stack:
        low, high = stack.pop()
        if low >= high:
            continue
        
        # Partition with simple pivot for robustness
        pivot = a[high]
        i = low - 1
        for j in range(low, high):
            comparisons += 1
            if a[j] <= pivot:
                i += 1
                a[i], a[j] = a[j], a[i]
                swaps += 1
        a[i + 1], a[high] = a[high], a[i + 1]
        swaps += 1
        pivot_idx = i + 1

        # Push smaller partition first to optimize stack depth
        if pivot_idx - 1 - low < high - (pivot_idx + 1):
            stack.append((pivot_idx + 1, high))
            stack.append((low, pivot_idx - 1))
        else:
            stack.append((low, pivot_idx - 1))
            stack.append((pivot_idx + 1, high))

    total_ops = comparisons + swaps
    return a, comparisons, swaps, total_ops


def merge_sort(arr: List[int]) -> Tuple[List[int], int, int, int]:
    """
    Standard Merge Sort tracking comparisons and data assignments (buffer copies).
    Time Complexity: O(N log N), Space Complexity: O(N).
    """
    a = list(arr)
    comparisons = 0
    moves = 0

    def _merge_sort_helper(sub: List[int]) -> List[int]:
        nonlocal comparisons, moves
        if len(sub) <= 1:
            return sub

        mid = len(sub) // 2
        left = _merge_sort_helper(sub[:mid])
        right = _merge_sort_helper(sub[mid:])

        merged = []
        i = j = 0
        while i < len(left) and j < len(right):
            comparisons += 1
            moves += 1
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                j += 1

        while i < len(left):
            moves += 1
            merged.append(left[i])
            i += 1
        while j < len(right):
            moves += 1
            merged.append(right[j])
            j += 1

        return merged

    sorted_arr = _merge_sort_helper(a)
    total_ops = comparisons + moves
    return sorted_arr, comparisons, moves, total_ops


def heap_sort(arr: List[int]) -> Tuple[List[int], int, int, int]:
    """
    In-place Heap Sort tracking comparisons and swaps during max-heapify.
    Time Complexity: O(N log N), Space Complexity: O(1).
    """
    a = list(arr)
    n = len(a)
    comparisons = 0
    swaps = 0

    def _heapify(length: int, root: int):
        nonlocal comparisons, swaps
        largest = root
        left = 2 * root + 1
        right = 2 * root + 2

        if left < length:
            comparisons += 1
            if a[left] > a[largest]:
                largest = left

        if right < length:
            comparisons += 1
            if a[right] > a[largest]:
                largest = right

        if largest != root:
            a[root], a[largest] = a[largest], a[root]
            swaps += 1
            _heapify(length, largest)

    # Build max-heap
    for i in range(n // 2 - 1, -1, -1):
        _heapify(n, i)

    # Extract elements one by one
    for i in range(n - 1, 0, -1):
        a[i], a[0] = a[0], a[i]
        swaps += 1
        _heapify(i, 0)

    total_ops = comparisons + swaps
    return a, comparisons, swaps, total_ops


ALGORITHMS: Dict[str, Callable[[List[int]], Tuple[List[int], int, int, int]]] = {
    "bubble": bubble_sort,
    "quick": quick_sort,
    "merge": merge_sort,
    "heap": heap_sort,
}

ALGORITHM_LABELS = {
    "bubble": "Bubble Sort (O(N^2))",
    "quick": "Quick Sort (O(N log N))",
    "merge": "Merge Sort (O(N log N))",
    "heap": "Heap Sort (O(N log N))",
}
