"""
Tests for StatisticsExtractor and related functions
"""

import numpy as np
import pytest
from astropy.table import Table
from astropy.time import Time

from ctapipe.calib.camera.extractor import PlainExtractor, SigmaClippingExtractor


def test_extractors(example_subarray):
    """test basic functionality of the StatisticsExtractors"""

    # Create dummy data for testing
    times = Time(
        np.linspace(60117.911, 60117.9258, num=5000), scale="tai", format="mjd"
    )
    ped_data = np.random.normal(2.0, 5.0, size=(5000, 2, 1855))
    charge_data = np.random.normal(77.0, 10.0, size=(5000, 2, 1855))
    time_data = np.random.normal(18.0, 5.0, size=(5000, 2, 1855))
    # Create tables
    ped_table = Table(
        [times, ped_data],
        names=("time_mono", "image"),
    )
    charge_table = Table(
        [times, charge_data],
        names=("time_mono", "image"),
    )
    time_table = Table(
        [times, time_data],
        names=("time_mono", "peak_time"),
    )
    # Initialize the extractors
    chunk_size = 2500
    ped_extractor = SigmaClippingExtractor(
        subarray=example_subarray, chunk_size=chunk_size
    )
    ff_charge_extractor = SigmaClippingExtractor(
        subarray=example_subarray, chunk_size=chunk_size
    )
    ff_time_extractor = PlainExtractor(subarray=example_subarray, chunk_size=chunk_size)

    # Extract the statistical values
    ped_stats = ped_extractor(table=ped_table)
    charge_stats = ff_charge_extractor(table=charge_table)
    time_stats = ff_time_extractor(table=time_table, col_name="peak_time")
    # Check if the calculated statistical values are reasonable
    # for a camera with two gain channels
    assert not np.any(np.abs(ped_stats[times[0]].mean - 2.0) > 1.5)
    assert not np.any(np.abs(charge_stats[times[0]].mean - 77.0) > 1.5)
    assert not np.any(np.abs(time_stats[times[0]].mean - 18.0) > 1.5)

    assert not np.any(np.abs(ped_stats[times[chunk_size]].median - 2.0) > 1.5)
    assert not np.any(np.abs(charge_stats[times[chunk_size]].median - 77.0) > 1.5)
    assert not np.any(np.abs(time_stats[times[chunk_size]].median - 18.0) > 1.5)

    assert not np.any(np.abs(ped_stats[times[0]].std - 5.0) > 1.5)
    assert not np.any(np.abs(charge_stats[times[0]].std - 10.0) > 1.5)
    assert not np.any(np.abs(time_stats[times[0]].std - 5.0) > 1.5)


def test_check_chunk_shift(example_subarray):
    """test the chunk shift option and the boundary case for the last chunk"""

    # Create dummy data for testing
    times = Time(
        np.linspace(60117.911, 60117.9258, num=5500), scale="tai", format="mjd"
    )
    charge_data = np.random.normal(77.0, 10.0, size=(5500, 2, 1855))
    # Create table
    charge_table = Table(
        [times, charge_data],
        names=("time_mono", "image"),
    )
    # Initialize the extractor
    extractor = SigmaClippingExtractor(subarray=example_subarray, chunk_size=2500)
    # Extract the statistical values
    chunk_stats = extractor(table=charge_table)
    chunk_stats_shift = extractor(table=charge_table, chunk_shift=2000)
    # Check if three chunks are used for the extraction as the last chunk overflows
    assert len(chunk_stats) == 3
    # Check if two chunks are used for the extraction as the last chunk is dropped
    assert len(chunk_stats_shift) == 2
    # Check if ValueError is raised when the chunk_size is larger than the length of table
    with pytest.raises(ValueError):
        _ = extractor(table=charge_table[1000:1500])
    # Check if ValueError is raised when the chunk_shift is smaller than the chunk_size
    with pytest.raises(ValueError):
        _ = extractor(table=charge_table, chunk_shift=3000)
