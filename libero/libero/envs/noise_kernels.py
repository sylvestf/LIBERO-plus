# numba versions of the loops in glass_blur and zoom_blur (env_wrapper.py), with the same output
import numpy as np

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

if NUMBA_AVAILABLE:

    @njit
    def _shuffle(x, offsets, max_delta, iterations):
        height, width, channels = x.shape
        k = 0
        for _ in range(iterations):
            for h in range(height - max_delta, max_delta, -1):
                for w in range(width - max_delta, max_delta, -1):
                    h_prime, w_prime = h + offsets[k, 1], w + offsets[k, 0]
                    k += 1
                    # same as the "swap" in glass_blur, which copies x[h', w'] into x[h, w]
                    for ch in range(channels):
                        x[h, w, ch] = x[h_prime, w_prime, ch]
        return x

    def shuffle_pixels(x, max_delta, iterations):
        height, width = x.shape[0], x.shape[1]
        visits = len(range(height - max_delta, max_delta, -1)) * len(range(width - max_delta, max_delta, -1))
        # one draw gives the same (dx, dy) values as one randint call per visit
        offsets = np.random.randint(-max_delta, max_delta, size=(iterations * visits, 2))
        return _shuffle(x, offsets, max_delta, iterations)

    @njit
    def _axis_weights(n_in, n_out):
        # sample positions and weights as scipy.ndimage.zoom(order=1, mode="constant") computes them
        start = np.empty(n_out, np.int64)
        after = np.empty(n_out, np.int64)
        w0 = np.empty(n_out, np.float64)
        w1 = np.empty(n_out, np.float64)
        inside = np.empty(n_out, np.bool_)
        step = (n_in - 1) / (n_out - 1) if n_out > 1 else 0.0
        for o in range(n_out):
            coord = o * step
            # rounding can put the last coordinate past the input; scipy gives cval (0) there
            inside[o] = coord <= n_in - 1
            k = min(int(np.floor(coord)), n_in - 1)
            start[o] = k
            after[o] = k + 1 if k + 1 < n_in else max(n_in - 2, 0)
            w0[o] = 1.0 - (coord - k)
            w1[o] = 1.0 - w0[o]
        return start, after, w0, w1, inside

    @njit
    def _zoom_sum(x, tops, trims, start, after, w0, w1, inside, out):
        height, width, channels = x.shape
        for y in range(height):
            for xx in range(width):
                # add the zoomed images in order, in float32, as zoom_blur does
                for k in range(tops.shape[0]):
                    i, j = y + trims[k], xx + trims[k]
                    if not (inside[k, i] and inside[k, j]):
                        continue
                    a0, a1, b0, b1 = tops[k] + start[k, i], tops[k] + after[k, i], tops[k] + start[k, j], tops[k] + after[k, j]
                    for c in range(channels):
                        out[y, xx, c] = np.float32(out[y, xx, c] + np.float32(
                            x[a0, b0, c] * w0[k, i] * w0[k, j] + x[a0, b1, c] * w0[k, i] * w1[k, j]
                            + x[a1, b0, c] * w1[k, i] * w0[k, j] + x[a1, b1, c] * w1[k, i] * w1[k, j]))
        return out

    def zoom_sum(x, factors, out):
        h = x.shape[0]
        crops = [int(np.ceil(h / float(z))) for z in factors]
        sizes = [int(round(ch * z)) for ch, z in zip(crops, factors)]
        shape = (len(factors), max(sizes))
        start, after = np.zeros(shape, np.int64), np.zeros(shape, np.int64)
        w0, w1, inside = np.zeros(shape), np.zeros(shape), np.zeros(shape, np.bool_)
        for k, (ch, size) in enumerate(zip(crops, sizes)):
            start[k, :size], after[k, :size], w0[k, :size], w1[k, :size], inside[k, :size] = _axis_weights(ch, size)
        tops = np.array([(h - ch) // 2 for ch in crops], np.int64)
        trims = np.array([(size - h) // 2 for size in sizes], np.int64)
        return _zoom_sum(np.ascontiguousarray(x), tops, trims, start, after, w0, w1, inside, out)
