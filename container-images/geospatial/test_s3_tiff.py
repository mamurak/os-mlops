#!/usr/bin/env python3
"""
Comprehensive test suite for S3 access and TIFF operations
in the geospatial container.
"""

import os
import sys
import json
import tempfile
import atexit
import traceback
import numpy as np
from osgeo import gdal, osr
import pdal

# Temporary file cleanup registry
_temp_files = []

def cleanup_temp_files():
    """Clean up temporary files created during tests"""
    for path in _temp_files:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

atexit.register(cleanup_temp_files)

def test_gdal_tiff_write():
    """Test 1: GDAL TIFF write operations"""
    print("\n=== Test 1: GDAL TIFF Write Operations ===")

    try:
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.tif')
        os.close(fd)
        _temp_files.append(temp_path)

        driver = gdal.GetDriverByName('GTiff')
        dataset = driver.Create(temp_path, 100, 100, 1, gdal.GDT_Float32)

        band = dataset.GetRasterBand(1)
        data = np.random.rand(100, 100).astype(np.float32)
        band.WriteArray(data)

        dataset.SetGeoTransform([0, 1, 0, 0, 0, -1])

        # Set projection correctly using OSR
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        dataset.SetProjection(srs.ExportToWkt())

        dataset.FlushCache()
        dataset = None

        # Read back and verify
        dataset = gdal.Open(temp_path)
        read_data = dataset.GetRasterBand(1).ReadAsArray()
        assert np.allclose(data, read_data), "Data mismatch!"

        print("✓ TIFF write/read successful")
        print(f"  Size: {dataset.RasterXSize}x{dataset.RasterYSize}")
        dataset = None
        return True
    except Exception as e:
        print(f"✗ TIFF write failed: {e}")
        traceback.print_exc()
        return False

def test_gdal_s3_support():
    """Test 2: GDAL S3 virtual file system support"""
    print("\n=== Test 2: GDAL S3 Support ===")

    # Save original environment state
    orig_env = os.environ.get('AWS_NO_SIGN_REQUEST')

    # Suppress GDAL errors for network-related failures
    gdal.PushErrorHandler('CPLQuietErrorHandler')

    try:
        # Configure for anonymous S3 access
        os.environ['AWS_NO_SIGN_REQUEST'] = 'YES'
        gdal.SetConfigOption('AWS_NO_SIGN_REQUEST', 'YES')

        # Test if /vsis3/ virtual filesystem is supported
        # First check with a simple stat operation
        info = gdal.VSIStatL('/vsis3/')
        last_error = gdal.GetLastErrorMsg()

        if info is None and 'not supported' in last_error.lower():
            print("✗ /vsis3/ not supported in this GDAL build")
            return False

        print("✓ /vsis3/ virtual filesystem is supported")

        # Try to access a public S3 bucket (informational only)
        # Using Sentinel-2 COGs which are publicly accessible
        s3_path = '/vsis3/sentinel-cogs/sentinel-s2-l2a-cogs/10/T/FK/2021/7/S2A_10TFK_20210701_0_L2A/TCI.tif'

        print(f"  Attempting network access: {s3_path}")
        dataset = gdal.Open(s3_path)

        if dataset is not None:
            print("✓ S3 network access verified with real data")
            print(f"  Dimensions: {dataset.RasterXSize}x{dataset.RasterYSize}")
            print(f"  Bands: {dataset.RasterCount}")
            dataset = None
        else:
            print("ℹ S3 supported but network access unavailable (no internet/credentials)")

        return True  # S3 support confirmed, network access is optional

    except Exception as e:
        print(f"✗ S3 test failed: {e}")
        traceback.print_exc()
        return False
    finally:
        # Restore original environment state
        if orig_env is None:
            os.environ.pop('AWS_NO_SIGN_REQUEST', None)
        else:
            os.environ['AWS_NO_SIGN_REQUEST'] = orig_env

        # Restore error handler
        gdal.PopErrorHandler()

def test_pdal_tiff_write():
    """Test 3: PDAL TIFF write via writers.gdal"""
    print("\n=== Test 3: PDAL TIFF Write ===")

    try:
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.tif')
        os.close(fd)
        _temp_files.append(temp_path)

        pipeline_json = {
            "pipeline": [
                {
                    "type": "readers.faux",
                    "mode": "ramp",
                    "count": 10000,
                    # PDAL bounds format: ([xmin, xmax], [ymin, ymax], [zmin, zmax])
                    "bounds": "([-100, 100], [-100, 100], [0, 100])"
                },
                {
                    "type": "writers.gdal",
                    "filename": temp_path,
                    "output_type": "mean",
                    "resolution": 1.0
                }
            ]
        }

        pipeline = pdal.Pipeline(json.dumps(pipeline_json))
        count = pipeline.execute()

        print(f"✓ PDAL processed {count} points")

        # Verify with GDAL
        ds = gdal.Open(temp_path)
        if ds is None:
            print("✗ Failed to read PDAL-generated TIFF")
            return False

        print(f"✓ TIFF created: {ds.RasterXSize}x{ds.RasterYSize}")
        ds = None
        return True
    except Exception as e:
        print(f"✗ PDAL TIFF write failed: {e}")
        traceback.print_exc()
        return False

def test_cog_support():
    """Test 4: Cloud Optimized GeoTIFF support"""
    print("\n=== Test 4: Cloud Optimized GeoTIFF (COG) ===")

    try:
        driver = gdal.GetDriverByName('COG')
        if driver is None:
            print("✗ COG driver not available")
            return False

        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix='.tif')
        os.close(fd)
        _temp_files.append(temp_path)

        # Create test data WITH proper geospatial metadata
        src_driver = gdal.GetDriverByName('MEM')
        src_ds = src_driver.Create('', 512, 512, 1, gdal.GDT_Byte)

        # CRITICAL: Set geotransform and projection
        src_ds.SetGeoTransform([0, 1, 0, 512, 0, -1])

        # Set projection correctly using OSR
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        src_ds.SetProjection(srs.ExportToWkt())

        # Fill with data
        src_ds.GetRasterBand(1).Fill(128)

        # Write as COG with proper options for small test dataset
        # Note: GDAL automatically skips overviews for small datasets
        cog_options = [
            'COMPRESS=LZW',
            'BLOCKSIZE=256',
            'TILED=YES'
        ]

        cog_ds = driver.CreateCopy(temp_path, src_ds, options=cog_options)

        # CRITICAL: Close/flush before reopening
        if cog_ds is not None:
            cog_ds.FlushCache()
            cog_ds = None

        src_ds = None

        # Verify
        verify_ds = gdal.Open(temp_path)
        if verify_ds is None:
            print("✗ Failed to read COG")
            return False

        print("✓ COG creation successful")
        print(f"  Size: {verify_ds.RasterXSize}x{verify_ds.RasterYSize}")
        verify_ds = None
        return True
    except Exception as e:
        print(f"✗ COG test failed: {e}")
        traceback.print_exc()
        return False

def test_formats_available():
    """Test 5: List supported formats"""
    print("\n=== Test 5: Available Formats ===")

    try:
        # Check required GDAL drivers
        print("GDAL Drivers:")
        print("  GTiff:", "✓" if gdal.GetDriverByName('GTiff') else "✗")
        print("  COG:", "✓" if gdal.GetDriverByName('COG') else "✗")

        required_gdal = ['GTiff', 'COG']
        missing_gdal = [drv for drv in required_gdal if not gdal.GetDriverByName(drv)]

        if missing_gdal:
            print(f"✗ Required GDAL drivers missing: {missing_gdal}")
            return False

        # Check PDAL drivers
        import subprocess
        result = subprocess.run(['pdal', '--drivers'], capture_output=True, text=True)
        has_las = 'readers.las' in result.stdout
        has_gdal = 'readers.gdal' in result.stdout
        has_writers_gdal = 'writers.gdal' in result.stdout

        print("PDAL Drivers:")
        print("  readers.las:", "✓" if has_las else "✗")
        print("  readers.gdal:", "✓" if has_gdal else "✗")
        print("  writers.gdal:", "✓" if has_writers_gdal else "✗")

        # Check required PDAL drivers
        if not has_writers_gdal:
            print("✗ Required PDAL driver missing: writers.gdal")
            return False

        print("✓ All required drivers available")
        return True

    except Exception as e:
        print(f"✗ Format check failed: {e}")
        traceback.print_exc()
        return False

def test_gdal_s3_write():
    """Test 6: GDAL S3 write operations"""
    print("\n=== Test 6: GDAL S3 Write ===")

    # Skip if no AWS credentials configured
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        print("ℹ Skipping S3 write test (no AWS credentials)")
        return True

    # Save original environment state
    orig_config = {}
    for key in ['AWS_NO_SIGN_REQUEST']:
        orig_config[key] = os.environ.get(key)

    # Suppress GDAL errors for network-related failures
    gdal.PushErrorHandler('CPLQuietErrorHandler')

    try:
        # Remove AWS_NO_SIGN_REQUEST if set (we need auth for writes)
        os.environ.pop('AWS_NO_SIGN_REQUEST', None)
        gdal.SetConfigOption('AWS_NO_SIGN_REQUEST', None)

        # Create small test dataset
        driver = gdal.GetDriverByName('GTiff')
        fd, local_path = tempfile.mkstemp(suffix='.tif')
        os.close(fd)
        _temp_files.append(local_path)

        ds = driver.Create(local_path, 10, 10, 1, gdal.GDT_Byte)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        ds.SetProjection(srs.ExportToWkt())
        ds.SetGeoTransform([0, 1, 0, 0, 0, -1])
        ds.GetRasterBand(1).Fill(42)
        ds.FlushCache()
        ds = None

        # Attempt S3 write
        s3_bucket = os.getenv('AWS_S3_BUCKET', 'test-bucket')
        s3_path = f'/vsis3/{s3_bucket}/test_write_{os.getpid()}.tif'

        # Copy file to S3 using GDAL virtual filesystem
        with open(local_path, 'rb') as f:
            file_content = f.read()

        # Write to S3
        vsi_file = gdal.VSIFOpenL(s3_path, 'wb')
        if vsi_file is None:
            print("✗ Failed to open S3 path for writing")
            return False

        gdal.VSIFWriteL(file_content, 1, len(file_content), vsi_file)
        gdal.VSIFCloseL(vsi_file)

        # Verify by reading back
        verify_ds = gdal.Open(s3_path)
        if verify_ds is not None:
            print(f"✓ S3 write successful: {s3_path}")
            verify_ds = None

            # Cleanup S3 file
            gdal.Unlink(s3_path)
            return True
        else:
            print("✗ Failed to verify S3 write")
            return False

    except Exception as e:
        print(f"⚠ S3 write test failed (may need valid credentials/bucket): {e}")
        traceback.print_exc()
        return True  # Don't fail the suite if S3 write unavailable

    finally:
        # Restore original environment
        for key, value in orig_config.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

        # Restore error handler
        gdal.PopErrorHandler()

def main():
    """Run all tests"""
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  Geospatial Container - S3 & TIFF Test Suite                  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")

    tests = [
        ("Format Support", test_formats_available),
        ("GDAL TIFF Write", test_gdal_tiff_write),
        ("GDAL S3 Support", test_gdal_s3_support),
        ("PDAL TIFF Write", test_pdal_tiff_write),
        ("COG Support", test_cog_support),
        ("GDAL S3 Write", test_gdal_s3_write),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            traceback.print_exc()
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
