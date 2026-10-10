"""
Unit tests for core.readers module

Tests input reading with validation, encoding handling, CSV detection,
URL scheme validation, SSRF protection, and error handling.
"""

import io
import zipfile
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET

import pytest
from PIL import Image
import pandas as pd
import requests

from core.readers import InputReader, InputValidationError, SSRFProtectionError


# Test fixtures

@pytest.fixture
def small_image_bytes():
    """Create a small valid image in memory."""
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def small_text_bytes():
    """Create small text content."""
    return b"This is a test text file.\nWith multiple lines.\n"


@pytest.fixture
def docx_bytes():
    """Create a minimal valid DOCX file."""
    # Create a minimal DOCX structure
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        # Minimal document.xml
        doc_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:t>First paragraph</w:t></w:p>
    <w:p><w:t>Second paragraph</w:t></w:p>
  </w:body>
</w:document>'''
        zf.writestr("word/document.xml", doc_xml)
    return buf.getvalue()


@pytest.fixture
def csv_bytes():
    """Create a simple CSV file."""
    csv_content = "id,text,value\n1,Hello world,10\n2,Test message,20\n3,Another post,30"
    return csv_content.encode("utf-8")


# Tests for read_image()

def test_read_image_valid(small_image_bytes):
    """Test reading a valid image."""
    img = InputReader.read_image(small_image_bytes, "test.png")
    
    assert isinstance(img, Image.Image)
    assert img.mode == "RGB"
    assert img.size == (100, 100)


def test_read_image_converts_to_rgb(small_image_bytes):
    """Test that images are converted to RGB mode."""
    # Create a grayscale image
    img_gray = Image.new("L", (50, 50), color=128)
    buf = io.BytesIO()
    img_gray.save(buf, format="PNG")
    
    img = InputReader.read_image(buf.getvalue(), "gray.png")
    assert img.mode == "RGB"


def test_read_image_too_large():
    """Test that oversized images are rejected."""
    # Create an image larger than MAX_FILE_SIZE
    large_data = b"x" * (InputReader.MAX_FILE_SIZE + 1)
    
    with pytest.raises(InputValidationError, match="exceeds maximum"):
        InputReader.read_image(large_data, "huge.png")


def test_read_image_invalid_data():
    """Test that invalid image data raises error."""
    invalid_data = b"This is not an image"
    
    with pytest.raises(InputValidationError, match="Could not read image"):
        InputReader.read_image(invalid_data, "bad.png")


# Tests for read_text_file()

def test_read_text_file_utf8(small_text_bytes):
    """Test reading UTF-8 encoded text."""
    text = InputReader.read_text_file(small_text_bytes, "test.txt")
    
    assert "This is a test text file" in text
    assert "With multiple lines" in text


def test_read_text_file_latin1():
    """Test reading Latin-1 encoded text."""
    text_latin1 = "Café résumé naïve".encode("latin-1")
    
    text = InputReader.read_text_file(text_latin1, "latin.txt")
    assert "Café" in text or "Caf" in text  # May have replacement chars


def test_read_text_file_with_encoding_errors():
    """Test that malformed encoding is handled gracefully."""
    # Mix valid UTF-8 with invalid bytes
    bad_bytes = b"Valid text \xFF\xFE invalid bytes"
    
    # Should not raise, but replace bad characters
    text = InputReader.read_text_file(bad_bytes, "bad_encoding.txt")
    assert "Valid text" in text


def test_read_text_file_too_large():
    """Test that oversized text files are rejected."""
    large_text = b"x" * (InputReader.MAX_FILE_SIZE + 1)
    
    with pytest.raises(InputValidationError, match="exceeds maximum"):
        InputReader.read_text_file(large_text, "huge.txt")


# Tests for read_docx()

def test_read_docx_text_extraction(docx_bytes):
    """Test extracting text from DOCX."""
    text, images = InputReader.read_docx(docx_bytes)
    
    assert "First paragraph" in text
    assert "Second paragraph" in text
    assert isinstance(images, list)


def test_read_docx_with_image():
    """Test extracting images from DOCX."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        # Minimal document.xml
        doc_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:t>Text with image</w:t></w:p></w:body>
</w:document>'''
        zf.writestr("word/document.xml", doc_xml)
        
        # Add a small image
        img = Image.new("RGB", (10, 10), color="blue")
        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        zf.writestr("word/media/image1.png", img_buf.getvalue())
    
    text, images = InputReader.read_docx(buf.getvalue())
    
    assert "Text with image" in text
    assert len(images) == 1
    assert images[0].mode == "RGB"


def test_read_docx_invalid_file():
    """Test that invalid DOCX files raise error."""
    not_a_docx = b"This is not a DOCX file"
    
    with pytest.raises(InputValidationError, match="not a valid DOCX"):
        InputReader.read_docx(not_a_docx)


def test_read_docx_missing_document_xml():
    """Test DOCX with missing document.xml."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr("some_other_file.xml", "<doc/>")
    
    with pytest.raises(InputValidationError, match="missing document.xml"):
        InputReader.read_docx(buf.getvalue())


def test_read_docx_too_large():
    """Test that oversized DOCX files are rejected."""
    large_data = b"x" * (InputReader.MAX_FILE_SIZE + 1)
    
    with pytest.raises(InputValidationError, match="exceeds maximum"):
        InputReader.read_docx(large_data)


# Tests for read_csv()

def test_read_csv_with_text_column(csv_bytes):
    """Test reading CSV and detecting text column."""
    texts, column_name = InputReader.read_csv(csv_bytes)
    
    assert column_name == "text"
    assert len(texts) == 3
    assert "Hello world" in texts
    assert "Test message" in texts
    assert "Another post" in texts


def test_read_csv_preferred_column_names():
    """Test that preferred column names are detected."""
    csv_content = "id,tweet,score\n1,First tweet,0.9\n2,Second tweet,0.8"
    csv_bytes = csv_content.encode("utf-8")
    
    texts, column_name = InputReader.read_csv(csv_bytes)
    
    assert column_name == "tweet"
    assert "First tweet" in texts


def test_read_csv_non_numeric_column():
    """Test detection of first non-numeric column."""
    csv_content = "num1,num2,description\n1,2,Text here\n3,4,More text"
    csv_bytes = csv_content.encode("utf-8")
    
    texts, column_name = InputReader.read_csv(csv_bytes)
    
    assert column_name == "description"
    assert "Text here" in texts


def test_read_csv_with_nulls():
    """Test that null values are dropped from CSV."""
    csv_content = "text\nFirst\n\nThird\n"
    csv_bytes = csv_content.encode("utf-8")
    
    texts, column_name = InputReader.read_csv(csv_bytes)
    
    assert len(texts) == 2
    assert "First" in texts
    assert "Third" in texts


def test_read_csv_empty_file():
    """Test that empty CSV raises error."""
    csv_content = ""
    csv_bytes = csv_content.encode("utf-8")
    
    with pytest.raises(InputValidationError, match="Could not parse CSV"):
        InputReader.read_csv(csv_bytes)


def test_read_csv_invalid_format():
    """Test that invalid CSV format raises error."""
    invalid_csv = b"This is not a CSV\x00\xFF"
    
    with pytest.raises(InputValidationError, match="Could not parse CSV"):
        InputReader.read_csv(invalid_csv)


def test_read_csv_too_large():
    """Test that oversized CSV files are rejected."""
    large_csv = b"x" * (InputReader.MAX_FILE_SIZE + 1)
    
    with pytest.raises(InputValidationError, match="exceeds maximum"):
        InputReader.read_csv(large_csv)


# Tests for URL scheme validation

def test_validate_url_scheme_http():
    """Test that HTTP URLs are accepted."""
    # Should not raise
    InputReader._validate_url_scheme("http://example.com")


def test_validate_url_scheme_https():
    """Test that HTTPS URLs are accepted."""
    # Should not raise
    InputReader._validate_url_scheme("https://example.com")


def test_validate_url_scheme_file():
    """Test that file:// URLs are rejected."""
    with pytest.raises(InputValidationError, match="not allowed"):
        InputReader._validate_url_scheme("file:///etc/passwd")


def test_validate_url_scheme_ftp():
    """Test that FTP URLs are rejected."""
    with pytest.raises(InputValidationError, match="not allowed"):
        InputReader._validate_url_scheme("ftp://ftp.example.com")


def test_validate_url_scheme_data():
    """Test that data: URLs are rejected."""
    with pytest.raises(InputValidationError, match="not allowed"):
        InputReader._validate_url_scheme("data:text/plain;base64,SGVsbG8=")


def test_validate_url_scheme_javascript():
    """Test that javascript: URLs are rejected."""
    with pytest.raises(InputValidationError, match="not allowed"):
        InputReader._validate_url_scheme("javascript:alert(1)")


# Tests for SSRF protection

def test_validate_url_host_localhost():
    """Test that localhost is blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://localhost")


def test_validate_url_host_127_0_0_1():
    """Test that 127.0.0.1 is blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://127.0.0.1")


def test_validate_url_host_private_10():
    """Test that 10.x.x.x private IPs are blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://10.0.0.1")


def test_validate_url_host_private_192_168():
    """Test that 192.168.x.x private IPs are blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://192.168.1.1")


def test_validate_url_host_private_172_16():
    """Test that 172.16-31.x.x private IPs are blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://172.16.0.1")


def test_validate_url_host_link_local():
    """Test that link-local IPs are blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://169.254.1.1")


def test_validate_url_host_ipv6_loopback():
    """Test that IPv6 loopback is blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://[::1]")


@patch("socket.getaddrinfo")
def test_validate_url_host_dns_to_private(mock_getaddrinfo):
    """Test that hostnames resolving to private IPs are blocked."""
    # Mock DNS resolution to return a private IP
    mock_getaddrinfo.return_value = [
        (2, 1, 6, '', ('192.168.1.1', 80))
    ]
    
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://evil.example.com")


@patch("socket.getaddrinfo")
def test_validate_url_host_public_ip_allowed(mock_getaddrinfo):
    """Test that public IPs are allowed."""
    # Mock DNS resolution to return a public IP (example.com)
    mock_getaddrinfo.return_value = [
        (2, 1, 6, '', ('93.184.216.34', 80))  # example.com IP
    ]
    
    # Should not raise
    InputReader._validate_url_host("http://example.com")


# Tests for fetch_url()

@patch("requests.get")
def test_fetch_url_image(mock_get, small_image_bytes):
    """Test fetching an image from URL."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/image.png"
    mock_response.headers = {"content-type": "image/png"}
    mock_response.iter_content = Mock(return_value=[small_image_bytes])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host"):
        img, text = InputReader.fetch_url("http://example.com/image.png")
    
    assert img is not None
    assert text is None
    assert img.mode == "RGB"


@patch("requests.get")
def test_fetch_url_text(mock_get):
    """Test fetching text from URL."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/page.txt"
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.iter_content = Mock(return_value=[b"Hello, world!"])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host"):
        img, text = InputReader.fetch_url("http://example.com/page.txt")
    
    assert img is None
    assert text is not None
    assert "Hello, world!" in text


@patch("requests.get")
def test_fetch_url_html_extraction(mock_get):
    """Test extracting text from HTML."""
    html_content = """
    <html>
    <head><title>Test</title></head>
    <body>
        <script>alert('test');</script>
        <p>This is a long paragraph with substantial content for testing.</p>
        <p>Another paragraph with enough text to be extracted properly.</p>
    </body>
    </html>
    """
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/page.html"
    mock_response.headers = {"content-type": "text/html"}
    mock_response.iter_content = Mock(return_value=[html_content.encode("utf-8")])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host"):
        img, text = InputReader.fetch_url("http://example.com/page.html")
    
    assert text is not None
    assert "long paragraph with substantial content" in text
    assert "alert" not in text  # Script removed


@patch("requests.get")
def test_fetch_url_timeout(mock_get):
    """Test that timeouts are handled properly."""
    mock_get.side_effect = requests.Timeout("Connection timed out")
    
    with patch.object(InputReader, "_validate_url_host"):
        with pytest.raises(InputValidationError, match="timed out"):
            InputReader.fetch_url("http://example.com/slow")


@patch("requests.get")
def test_fetch_url_size_limit(mock_get):
    """Test that content size limits are enforced."""
    # Create chunks that exceed MAX_URL_SIZE
    large_chunk = b"x" * (InputReader.MAX_URL_SIZE // 2 + 1)
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/large"
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.iter_content = Mock(return_value=[large_chunk, large_chunk])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host"):
        with pytest.raises(InputValidationError, match="exceeds maximum size"):
            InputReader.fetch_url("http://example.com/large")


@patch("requests.get")
def test_fetch_url_redirect_validation(mock_get):
    """Test that redirects are validated for SSRF."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://192.168.1.1/internal"  # Redirected to private IP
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.iter_content = Mock(return_value=[b"content"])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host") as mock_validate:
        # First call passes (original URL), second call should fail (redirect)
        mock_validate.side_effect = [None, SSRFProtectionError("Blocked")]
        
        with pytest.raises(SSRFProtectionError):
            InputReader.fetch_url("http://example.com/redirect")


@patch("requests.get")
def test_fetch_url_request_error(mock_get):
    """Test handling of request errors."""
    mock_get.side_effect = requests.RequestException("Network error")
    
    with patch.object(InputReader, "_validate_url_host"):
        with pytest.raises(InputValidationError, match="Failed to fetch URL"):
            InputReader.fetch_url("http://example.com/error")


def test_fetch_url_invalid_scheme():
    """Test that invalid schemes are rejected before fetch."""
    with pytest.raises(InputValidationError, match="not allowed"):
        InputReader.fetch_url("ftp://example.com/file")


def test_fetch_url_ssrf_protection():
    """Test that SSRF protection is enforced."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader.fetch_url("http://localhost/internal")


# Additional security tests

def test_validate_url_host_ipv4_mapped_ipv6():
    """Test that IPv4-mapped IPv6 loopback addresses are blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://[::ffff:127.0.0.1]")


def test_validate_url_host_ipv6_private():
    """Test that IPv6 private addresses are blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://[fc00::1]")


def test_validate_url_scheme_case_insensitive():
    """Test that scheme validation is case-insensitive."""
    # HTTP and HTTPS in various cases should be allowed
    InputReader._validate_url_scheme("HTTP://example.com")
    InputReader._validate_url_scheme("Https://example.com")
    InputReader._validate_url_scheme("HtTp://example.com")
    
    # Other schemes should still be blocked
    with pytest.raises(InputValidationError, match="not allowed"):
        InputReader._validate_url_scheme("FILE://etc/passwd")


def test_validate_url_host_empty_hostname():
    """Test that URLs without hostnames are rejected."""
    with pytest.raises(InputValidationError, match="must include a hostname"):
        InputReader._validate_url_host("http:///path")


def test_validate_url_host_with_port():
    """Test that private IPs with ports are blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://192.168.1.1:8080")


def test_validate_url_host_with_credentials():
    """Test URLs with credentials in hostname."""
    # Should extract hostname correctly and validate it
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://user:pass@192.168.1.1")


@patch("requests.get")
def test_fetch_url_multiple_redirects(mock_get):
    """Test that all redirects in a chain are validated."""
    # Create a redirect chain where second redirect goes to private IP
    mock_response = Mock()
    mock_response.status_code = 200
    # Simulate redirect to private IP
    mock_response.url = "http://10.0.0.1/internal"
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.iter_content = Mock(return_value=[b"content"])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host") as mock_validate:
        # First validation passes (original URL)
        # Second validation should catch the redirect to private IP
        def validate_side_effect(url):
            if "10.0.0.1" in url:
                raise SSRFProtectionError("Blocked redirect to private IP")
        
        mock_validate.side_effect = validate_side_effect
        
        with pytest.raises(SSRFProtectionError, match="private IP"):
            InputReader.fetch_url("http://example.com/redirect")


@patch("requests.get")
def test_fetch_url_slow_response(mock_get):
    """Test that slow responses don't hang indefinitely."""
    # Simulate a very slow response that exceeds timeout
    import time
    
    def slow_iter():
        time.sleep(0.1)
        yield b"slow"
        time.sleep(0.1)
        yield b"data"
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/slow"
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.iter_content = Mock(return_value=slow_iter())
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host"):
        # Should complete (chunks are small)
        img, text = InputReader.fetch_url("http://example.com/slow")
        assert text is not None


def test_validate_url_host_0_0_0_0():
    """Test that 0.0.0.0 is blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://0.0.0.0")


def test_validate_url_host_broadcast():
    """Test that broadcast address is blocked."""
    with pytest.raises(SSRFProtectionError, match="blocked"):
        InputReader._validate_url_host("http://255.255.255.255")


@patch("requests.get")
def test_fetch_url_no_content_type(mock_get):
    """Test fetching URL with no content-type header."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/file"
    mock_response.headers = {}  # No content-type
    mock_response.iter_content = Mock(return_value=[b"Some text content"])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host"):
        img, text = InputReader.fetch_url("http://example.com/file")
        # Should default to text parsing
        assert text is not None


@patch("requests.get")
def test_fetch_url_malformed_content_type(mock_get):
    """Test handling of malformed content-type headers."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.url = "http://example.com/file"
    mock_response.headers = {"content-type": "invalid;;;garbage"}
    mock_response.iter_content = Mock(return_value=[b"content"])
    mock_get.return_value = mock_response
    
    with patch.object(InputReader, "_validate_url_host"):
        # Should not crash
        img, text = InputReader.fetch_url("http://example.com/file")
        assert img is not None or text is not None
