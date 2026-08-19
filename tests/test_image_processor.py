import numpy as np
import pytest

from river_extractor.image_processor import calculate_ndwi, create_water_mask


def test_calculate_ndwi():
    green = np.array(
        [[0.6, 0.2]],
        dtype=np.float32,
    )
    nir = np.array(
        [[0.2, 0.6]],
        dtype=np.float32,
    )

    result = calculate_ndwi(green, nir)

    expected = np.array(
        [[0.5, -0.5]],
        dtype=np.float32,
    )

    np.testing.assert_allclose(result, expected, rtol=1e-6, atol=1e-7)

    def test_zero_denominator_becomes_nan():

        green = np.array(
            [[0.0]],
            dtype=np.float32,
        )
        nir = np.array(
            [[0.0]],
            dtype=np.float,
        )

        result = calculate_ndwi(green, nir)

        assert np.isnan(result[0, 0])

    def test_green_and_nir_shapes_must_match():
        green = np.ones(
            (2, 2),
            dtype=np.float32,
        )
        nir = np.ones(
            (3, 3),
            dtype=np.float32,
        )

        with pytest.raises(ValueError):
            calculate_ndwi(green, nir)

    def test_create_water_mask():
        ndwi = np.array(
            [[0.2, -0.1, np.nan]],
            dtype=np.float32,
        )
        result = create_water_mask(
            ndwi=ndwi,
            threshold=0.0,
        )

        expected = np.array(
            [[1, 0, 0]],
            dtype=np.uint8,
        )

        np.testing.assert_array_equal(result, expected)
