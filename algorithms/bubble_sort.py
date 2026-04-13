"""
bubble_sort.py - Bubble Sort algorithm with generator-based step visualization.

Yields state snapshots at each comparison/swap so the visualizer can
animate every step of the sort.
"""


def bubble_sort(array):
    """
    Generator that performs Bubble Sort on *array* **in-place**.

    At each meaningful step it yields a dictionary describing the current state:

        {
            "array":    list[int],   # current snapshot of the array
            "compare":  (i, j),      # indices currently being compared
            "swap":     (i, j)|None, # indices that were swapped (or None)
            "sorted":   set[int],    # indices known to be in final position
            "pass_num": int,         # current pass number (1-based)
        }

    Args:
        array (list): The list of integers to sort.

    Yields:
        dict: State snapshot after each comparison / swap.
    """
    n = len(array)
    sorted_indices = set()  # Track which positions are fully sorted

    for i in range(n - 1):
        swapped = False

        for j in range(n - 1 - i):
            # --- Comparison step ---
            yield {
                "array": array[:],       # snapshot (copy)
                "compare": (j, j + 1),
                "swap": None,
                "sorted": set(sorted_indices),
                "pass_num": i + 1,
            }

            if array[j] > array[j + 1]:
                # --- Swap step ---
                array[j], array[j + 1] = array[j + 1], array[j]
                swapped = True

                yield {
                    "array": array[:],
                    "compare": (j, j + 1),
                    "swap": (j, j + 1),
                    "sorted": set(sorted_indices),
                    "pass_num": i + 1,
                }

        # After each full pass the last unsorted element is in place
        sorted_indices.add(n - 1 - i)

        # Early termination – array already sorted
        if not swapped:
            sorted_indices.update(range(n))
            yield {
                "array": array[:],
                "compare": None,
                "swap": None,
                "sorted": set(sorted_indices),
                "pass_num": i + 1,
            }
            return

    # The very first element is also sorted
    sorted_indices.add(0)

    # Final "done" frame
    yield {
        "array": array[:],
        "compare": None,
        "swap": None,
        "sorted": set(sorted_indices),
        "pass_num": n - 1,
    }
