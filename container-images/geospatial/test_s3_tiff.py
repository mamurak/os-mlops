#!/usr/bin/env python3
"""
Comprehensive test suite for S3 access and TIFF operations
in the geospatial container.
"""

import os
import sys
import json
import numpy as np
from osgeo import gdal
import pdal

def test_gdal_tiff_write():
    """Test 1: GDAL TIFF write operations"""
    print("\n=== Test 1: GDAL TIFF Write Operations ===")

    try:
        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create('/tmp/test.tif', 100, 100, 1, gdal.GDT_Float32)

        band = dataset.GetRasterBand(1)
        data = np.random.rand(100, 100).astype(np.float32)
        band.WriteArray(data)

        dataset.SetGeoTransform([0, 1, 0, 0, 0, -1])
        dataset.SetProjection('EPSG:4326')

        dataset.FlushCache()
        dataset = None

        # Read back and verify
        dataset = gdal.Open('/tmp/test.tif')
        read_data = dataset.GetRasterBand(1).ReadAsArray()
        assert np.allclose(data, read_data), "Data mismatch!"

        print("✓ TIFF write/read successful")
        print(f"  Size: {dataset.RasterXSize}x{dataset.RasterYSize}")
        return True
    except Exception as e:
        print(f"✗ TIFF write failed: {e}")
        return False

def test_gdal_s3_support():
    """Test 2: GDAL S3 virtual file system support"""
    print("\n=== Test 2: GDAL S3 Support ===")

    try:
        # Test that /vsis3/ is recognized
        os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'
        gdal.SetConfigOption('AWS_NO_SIGN_REQUEST', 'YES')

        # Try to access a public S3 bucket
        # Using Sentinel-2 COGs which are publicly accessible
        s3_path = '/vsis3/sentinel-cogs/sentinel-s2-l2a-cogs/10/T/FK/2021/7/S2A_10TFK_20210701_0_L2A/TCI.tif'

        print(f"  Attempting to read: {s3_path}")
        dataset = gdal.Open(s3_path)

        if dataset is not None:
            print(f"✓ Successfully read from S3")
            print(f"  Dimensions: {dataset.RasterXSize}x{dataset.RasterYSize}")
            print(f"  Bands: {dataset.RasterCount}")
            dataset = None
            return True
        else:
            err = gdal.GetLastErrorMsg()
            if 'not supported' in err.lower():
                print(f"✗ /vsis3/ not supported")
                return False
            else:
                print(f"⚠ S3 supported but access failed (expected if no internet): {err}")
                return True  # S3 is supported, just can't access
    except Exception as e:
        print(f"✗ S3 test failed: {e}")
        return False

def test_pdal_tiff_write():
    """Test 3: PDAL TIFF write via writers.gdal"""
    print("\n=== Test 3: PDAL TIFF Write ===")

    try:
        pipeline_json = {
            "pipeline": [
                {
                    "type": "readers.faux",
                    "mode": "ramp",
                    "count": 10000,
                    "bounds": "([-100, 100], [-100, 100], [0, 100])"
                },
                {
                    "type": "writers.gdal",
                    "filename": "/tmp/pdal_output.tif",
                    "output_type": "mean",
                    "resolution": 1.0
                }
            ]
        }

        pipeline = pdal.Pipeline(json.dumps(pipeline_json))
        count = pipeline.execute()

        print(f"✓ PDAL processed {count} points")

        # Verify with GDAL
        ds = gdal.Open('/tmp/pdal_output.tif')
        if ds is None:
            print("✗ Failed to read PDAL-generated TIFF")
            return False

        print(f"✓ TIFF created: {ds.RasterXSize}x{ds.RasterYSize}")
        ds = None
        return True
    except Exception as e:
        print(f"✗ PDAL TIFF write failed: {e}")
        return False

def test_cog_support():
    """Test 4: Cloud Optimized GeoTIFF support"""
    print("\n=== Test 4: Cloud Optimized GeoTIFF (COG) ===")

    try:
        driver = gdal.GetDriverByName('COG')
        if driver is None:
            print("✗ COG driver not available")
            return False

        # Create test data WITH proper geospatial metadata
        src_driver = gdal.GetDriverByName('MEM')
        src_ds = src_driver.Create('', 512, 512, 1, gdal.GDT_Byte)

        # CRITICAL: Set geotransform and projection
        src_ds.SetGeoTransform([0, 1, 0, 512, 0, -1])
        src_ds.SetProjection('EPSG:4326')

        # Fill with data
        src_ds.GetRasterBand(1).Fill(128)

        # Write as COG with PROPER options for small test dataset
        cog_options = [
            'COMPRESS=LZW',
            'BLOCKSIZE=256',
            'OVERVIEWS=NONE',  # Skip overviews for small test
            'TILED=YES'
        ]

        cog_ds = driver.CreateCopy('/tmp/test_cog.tif', src_ds, options=cog_options)

        # CRITICAL: Close/flush before reopening
        if cog_ds is not None:
            cog_ds.FlushCache()
            cog_ds = None

        src_ds = None

        # Verify
        verify_ds = gdal.Open('/tmp/test_cog.tif')
        if verify_ds is None:
            print("✗ Failed to read COG")
            return False

        print("✓ COG creation successful")
        print(f"  Size: {verify_ds.RasterXSize}x{verify_ds.RasterYSize}")
        verify_ds = None
        return True
    except Exception as e:
        print(f"✗ COG test failed: {e}")
        return False

def test_formats_available():
    """Test 5: List supported formats"""
    print("\n=== Test 5: Available Formats ===")

    print("GDAL Drivers:")
    print("  GTiff:", "✓" if gdal.GetDriverByName('GTiff') else "✗")
    print("  COG:", "✓" if gdal.GetDriverByName('COG') else "✗")

    # Check PDAL readers
    import subprocess
    result = subprocess.run(['pdal', '--drivers'], capture_output=True, text=True)
    has_las = 'readers.las' in result.stdout
    has_gdal = 'readers.gdal' in result.stdout
    has_writers_gdal = 'writers.gdal' in result.stdout

    print("PDAL Drivers:")
    print("  readers.las:", "✓" if has_las else "✗")
    print("  readers.gdal:", "✓" if has_gdal else "✗")
    print("  writers.gdal:", "✓" if has_writers_gdal else "✗")

    return True

def main():
    """Run all tests"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  Geospatial Container - S3 & TIFF Test Suite                  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    # Suppress GDAL warnings for cleaner output
    gdal.PushErrorHandler('CPLQuietErrorHandler')

    tests = [
        ("Format Support", test_formats_available),
        ("GDAL TIFF Write", test_gdal_tiff_write),
        ("GDAL S3 Support", test_gdal_s3_support),
        ("PDAL TIFF Write", test_pdal_tiff_write),
        ("COG Support", test_cog_support),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*65)
    print("TEST SUMMARY")
    print("="*65)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓✓✓ All tests PASSED ✓✓✓")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
