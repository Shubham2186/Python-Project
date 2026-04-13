"""
merge_sort.py - Merge Sort algorithm with generator-based step visualization.

Yields state snapshots at every comparison / write-back so the visualizer
can animate the entire merge sort process.
"""


def merge_sort(array):
    """
    Generator that performs Merge Sort on *array* **in-place**.

    Yields state dictionaries:

        {
            "array":        list[int],      # current array snapshot
            "compare":      (i, j)|None,    # indices being compared
            "swap":         int|None,       # index being written to
            "sorted":       set[int],       # fully-sorted indices
            "active_range": (lo, hi)|None,  # sub-array currently being merged
        }

    Args:
        array (list): The list of integers to sort.

    Yields:
        dict: State snapshot.
    """
    if len(array) <= 1:
        yield {
            "array": array[:],
            "compare": None,
            "swap": None,
            "sorted": set(range(len(array))),
            "active_range": None,
        }
        return

    # We use an *iterative* helper so we can yield from a single generator
    # without recursive yield-from chains (keeps the code beginner-friendly).
    yield from _merge_sort_iterative(array)


def _merge_sort_iterative(array):
    """
    Bottom-up (iterative) merge sort that yields visualization states.

    This avoids deep recursion and makes it easy to yield at each step.

    Args:
        array (list): The list to sort in-place.

    Yields:
        dict: State snapshot.
    """
    n = len(array)
    sorted_indices = set()

    # Width of sub-arrays to merge: 1, 2, 4, 8, ...
    width = 1

    while width < n:
        for start in range(0, n, 2 * width):
            mid = min(start + width, n)
            end = min(start + 2 * width, n)

            # Merge array[start:mid] and array[mid:end]
            yield from _merge(array, start, mid, end, sorted_indices)

        width *= 2

    # Mark everything sorted at the end
    sorted_indices = set(range(n))
    yield {
        "array": array[:],
        "compare": None,
        "swap": None,
        "sorted": sorted_indices,
        "active_range": None,
    }


def _merge(array, start, mid, end, sorted_indices):
    """
    Merge two adjacent sorted sub-arrays and yield each step.

    Args:
        array (list): The full array.
        start (int): Start index of the left half.
        mid (int):   Start index of the right half.
        end (int):   One-past-the-end index of the right half.
        sorted_indices (set): Indices that are fully sorted so far.

    Yields:
        dict: State snapshot.
    """
    # Create temporary copies of the two halves
    left = array[start:mid]
    right = array[mid:end]

    i = 0  # pointer into left
    j = 0  # pointer into right
    k = start  # pointer into original array

    while i < len(left) and j < len(right):
        # Show comparison between elements from left and right halves
        left_idx = start + i
        right_idx = mid + j

        yield {
            "array": array[:],
            "compare": (left_idx, right_idx),
            "swap": None,
            "sorted": set(sorted_indices),
            "active_range": (start, end - 1),
        }

        if left[i] <= right[j]:
            array[k] = left[i]
            i += 1
        else:
            array[k] = right[j]
            j += 1

        # Show the write-back
        yield {
            "array": array[:],
            "compare": None,
            "swap": k,
            "sorted": set(sorted_indices),
            "active_range": (start, end - 1),
        }
        k += 1

    # Copy remaining elements from left half
    while i < len(left):
        array[k] = left[i]
        yield {
            "array": array[:],
            "compare": None,
            "swap": k,
            "sorted": set(sorted_indices),
            "active_range": (start, end - 1),
        }
        i += 1
        k += 1

    # Copy remaining elements from right half
    while j < len(right):
        array[k] = right[j]
        yield {
            "array": array[:],
            "compare": None,
            "swap": k,
            "sorted": set(sorted_indices),
            "active_range": (start, end - 1),
        }
        j += 1
        k += 1
