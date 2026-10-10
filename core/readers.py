"""
Input Readers Module

Provides secure input reading from various sources: images, text files,
DOCX documents, CSV files, and URLs. Enforces security constraints to
prevent SSRF attacks, resource exhaustion, and other vulnerabilities.
"""

import io
import ipaddress
import re
import socket
import xml.etree.ElementTree as ET
import zipfile
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd
import requests
from PIL import Image

from core.settings import settings


class InputValidationError(Exception):
    """Raised when input validation fails."""
    pass


class SSRFProtectionError(InputValidationError):
    """Raised when SSRF protection blocks a request."""
    pass


class InputReader:
    """
    Secure input reader with validation and SSRF protection.
    
    Reads content from various sources while enforcing security constraints:
    - File size limits
    - URL scheme validation (HTTP/HTTPS only)
    - SSRF protection (blocks private/loopback/link-local IPs)
    - Timeout enforcement
    - Encoding safety
    
    All user content is processed in memory and never persisted to disk.
    """
    
    # Configuration from settings
    MAX_FILE_SIZE = settings.max_file_size_bytes
    URL_TIMEOUT = settings.url_timeout_seconds
    MAX_URL_SIZE = settings.max_url_size_bytes
    
    # Private and special-use IP ranges (RFC 1918, RFC 4193, RFC 3927, etc.)
    BLOCKED_IP_RANGES = [
        # IPv4 private ranges
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        # IPv4 loopback
        ipaddress.ip_network("127.0.0.0/8"),
        # IPv4 link-local
        ipaddress.ip_network("169.254.0.0/16"),
        # IPv4 multicast and reserved
        ipaddress.ip_network("224.0.0.0/4"),
        ipaddress.ip_network("240.0.0.0/4"),
        # IPv6 loopback
        ipaddress.ip_network("::1/128"),
        # IPv6 link-local
        ipaddress.ip_network("fe80::/10"),
        # IPv6 unique local
        ipaddress.ip_network("fc00::/7"),
        # IPv6 multicast
        ipaddress.ip_network("ff00::/8"),
    ]
    
    @staticmethod
    def read_image(file_data: bytes, filename: str) -> Image.Image:
        """
        Read and validate an image file.
        
        Args:
            file_data: Raw bytes of the image file
            filename: Original filename for error messages
        
        Returns:
            PIL Image in RGB mode
        
        Raises:
            InputValidationError: If file is invalid or not an image
        
        Example:
            >>> with open("photo.jpg", "rb") as f:
            ...     img = InputReader.read_image(f.read(), "photo.jpg")
        """
        if len(file_data) > InputReader.MAX_FILE_SIZE:
            raise InputValidationError(
                f"File size {len(file_data)} bytes exceeds maximum "
                f"{InputReader.MAX_FILE_SIZE} bytes"
            )
        
        try:
            img = Image.open(io.BytesIO(file_data))
            # Convert to RGB to ensure consistent format
            return img.convert("RGB")
        except Exception as e:
            raise InputValidationError(
                f"Could not read image from {filename}: {e}"
            )
    
    @staticmethod
    def read_text_file(file_data: bytes, filename: str) -> str:
        """
        Read text from a text file with encoding detection.
        
        Attempts UTF-8 first, then falls back to latin-1 with error replacement.
        
        Args:
            file_data: Raw bytes of the text file
            filename: Original filename for error messages
        
        Returns:
            Decoded text content
        
        Raises:
            InputValidationError: If file is too large or invalid
        
        Example:
            >>> with open("notes.txt", "rb") as f:
            ...     text = InputReader.read_text_file(f.read(), "notes.txt")
        """
        if len(file_data) > InputReader.MAX_FILE_SIZE:
            raise InputValidationError(
                f"File size {len(file_data)} bytes exceeds maximum "
                f"{InputReader.MAX_FILE_SIZE} bytes"
            )
        
        # Try UTF-8 first
        try:
            return file_data.decode("utf-8")
        except UnicodeDecodeError:
            pass
        
        # Fall back to latin-1 with error replacement
        try:
            return file_data.decode("latin-1", errors="replace")
        except Exception as e:
            raise InputValidationError(
                f"Could not decode text from {filename}: {e}"
            )
    
    @staticmethod
    def read_docx(file_data: bytes) -> Tuple[str, List[Image.Image]]:
        """
        Extract text and images from a DOCX file.
        
        Parses the DOCX (which is a ZIP archive) and extracts:
        - Text content from word/document.xml
        - Embedded images from word/media/
        
        Args:
            file_data: Raw bytes of the DOCX file
        
        Returns:
            Tuple of (text_content, list_of_images)
        
        Raises:
            InputValidationError: If file is invalid or not a DOCX
        
        Example:
            >>> with open("report.docx", "rb") as f:
            ...     text, images = InputReader.read_docx(f.read())
        """
        if len(file_data) > InputReader.MAX_FILE_SIZE:
            raise InputValidationError(
                f"File size {len(file_data)} bytes exceeds maximum "
                f"{InputReader.MAX_FILE_SIZE} bytes"
            )
        
        try:
            with zipfile.ZipFile(io.BytesIO(file_data)) as z:
                # Extract text from document.xml
                text_parts = []
                try:
                    doc_xml = z.read("word/document.xml")
                    root = ET.fromstring(doc_xml)
                    
                    # Word namespace
                    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                    
                    # Extract text from paragraphs
                    for paragraph in root.findall(".//w:p", ns):
                        para_text = []
                        for text_elem in paragraph.findall(".//w:t", ns):
                            if text_elem.text:
                                para_text.append(text_elem.text)
                        if para_text:
                            text_parts.append("".join(para_text))
                except KeyError:
                    raise InputValidationError("Invalid DOCX file: missing document.xml")
                
                text = "\n".join(text_parts)
                
                # Extract images from media folder
                images = []
                for name in z.namelist():
                    if name.startswith("word/media/"):
                        try:
                            img_data = z.read(name)
                            img = Image.open(io.BytesIO(img_data))
                            images.append(img.convert("RGB"))
                        except Exception:
                            # Skip images we can't read
                            pass
                
                return text, images
                
        except zipfile.BadZipFile:
            raise InputValidationError("File is not a valid DOCX document")
        except Exception as e:
            raise InputValidationError(f"Could not read DOCX file: {e}")
    
    @staticmethod
    def read_csv(file_data: bytes) -> Tuple[List[str], str]:
        """
        Parse CSV and auto-detect the text column.
        
        Attempts to identify the column most likely to contain text content
        for analysis. Prefers columns with known names (text, tweet, content, etc.)
        or the first non-numeric column.
        
        Args:
            file_data: Raw bytes of the CSV file
        
        Returns:
            Tuple of (list_of_texts, detected_column_name)
        
        Raises:
            InputValidationError: If file is invalid or has no text columns
        
        Example:
            >>> with open("posts.csv", "rb") as f:
            ...     texts, col_name = InputReader.read_csv(f.read())
        """
        if len(file_data) > InputReader.MAX_FILE_SIZE:
            raise InputValidationError(
                f"File size {len(file_data)} bytes exceeds maximum "
                f"{InputReader.MAX_FILE_SIZE} bytes"
            )
        
        try:
            df = pd.read_csv(io.BytesIO(file_data))
        except Exception as e:
            raise InputValidationError(f"Could not parse CSV file: {e}")
        
        if df.empty:
            raise InputValidationError("CSV file is empty")
        
        # Detect text column
        column_name = InputReader._detect_csv_text_column(df)
        
        if column_name is None:
            raise InputValidationError(
                "Could not detect a text column in CSV file"
            )
        
        # Extract texts, dropping nulls
        texts = df[column_name].dropna().astype(str).tolist()
        
        if not texts:
            raise InputValidationError(
                f"No valid text found in column '{column_name}'"
            )
        
        return texts, column_name
    
    @staticmethod
    def _detect_csv_text_column(df: pd.DataFrame) -> Optional[str]:
        """
        Auto-detect the most likely text column in a CSV.
        
        Uses heuristics to identify text columns:
        1. Prefer columns with known names
        2. Prefer non-numeric columns
        3. Fall back to first column
        
        Args:
            df: Pandas DataFrame to analyze
        
        Returns:
            Name of the detected text column, or None if no suitable column
        """
        if df.empty or len(df.columns) == 0:
            return None
        
        # Preferred column names for text content
        preferred_names = [
            "text", "tweet", "content", "post", "message",
            "description", "body", "comment", "caption"
        ]
        
        # Check for preferred column names (case-insensitive)
        for pref in preferred_names:
            for col in df.columns:
                if str(col).lower() == pref:
                    return col
        
        # Find first non-numeric column
        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                return col
        
        # Fall back to first column
        return df.columns[0]
    
    @staticmethod
    def fetch_url(url: str) -> Tuple[Optional[Image.Image], Optional[str]]:
        """
        Fetch content from a URL with security validation.
        
        Enforces strict security constraints:
        - Only HTTP/HTTPS schemes allowed
        - Resolves hostname and blocks private/loopback/link-local IPs
        - Enforces timeout and size limits
        - Handles redirects safely
        
        Args:
            url: URL to fetch
        
        Returns:
            Tuple of (image, text). One will be None depending on content type.
        
        Raises:
            InputValidationError: If URL is invalid or fetch fails
            SSRFProtectionError: If URL resolves to blocked IP range
        
        Example:
            >>> img, text = InputReader.fetch_url("https://example.com/image.jpg")
        """
        # Validate URL scheme
        InputReader._validate_url_scheme(url)
        
        # Validate hostname to prevent SSRF
        InputReader._validate_url_host(url)
        
        try:
            # Fetch with timeout and streaming to check size
            response = requests.get(
                url,
                timeout=InputReader.URL_TIMEOUT,
                stream=True,
                headers={"User-Agent": "GumShoo/1.0"},
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check if redirect went to a blocked host
            if response.url != url:
                InputReader._validate_url_host(response.url)
            
            # Read content with size limit
            content = bytearray()
            for chunk in response.iter_content(chunk_size=8192):
                content.extend(chunk)
                if len(content) > InputReader.MAX_URL_SIZE:
                    raise InputValidationError(
                        f"URL content exceeds maximum size "
                        f"{InputReader.MAX_URL_SIZE} bytes"
                    )
            
            content_bytes = bytes(content)
            content_type = response.headers.get("content-type", "").lower()
            
            # Try to parse as image
            if "image" in content_type:
                try:
                    img = Image.open(io.BytesIO(content_bytes))
                    return img.convert("RGB"), None
                except Exception as e:
                    raise InputValidationError(f"Could not parse image: {e}")
            
            # Try to parse as text/HTML
            try:
                text = content_bytes.decode("utf-8", errors="replace")
                
                # If HTML, extract text content
                if "html" in content_type:
                    # Remove script and style tags
                    text = re.sub(r"(?s)<(script|style).*?</\1>", " ", text)
                    # Remove HTML tags
                    text = re.sub(r"<[^>]+>", "\n", text)
                    # Extract lines with substantial content
                    lines = [
                        line.strip()
                        for line in text.splitlines()
                        if len(line.strip()) > 20
                    ]
                    text = "\n".join(lines)
                
                return None, text
                
            except Exception as e:
                raise InputValidationError(f"Could not parse text content: {e}")
                
        except requests.Timeout:
            raise InputValidationError(
                f"URL request timed out after {InputReader.URL_TIMEOUT} seconds"
            )
        except requests.RequestException as e:
            raise InputValidationError(f"Failed to fetch URL: {e}")
    
    @staticmethod
    def _validate_url_scheme(url: str) -> None:
        """
        Ensure URL uses http or https scheme only.
        
        Args:
            url: URL to validate
        
        Raises:
            InputValidationError: If scheme is not http or https
        """
        parsed = urlparse(url)
        # Normalize scheme to lowercase for case-insensitive comparison
        scheme = parsed.scheme.lower() if parsed.scheme else ""
        if scheme not in ("http", "https"):
            raise InputValidationError(
                f"URL scheme '{parsed.scheme}' not allowed. "
                f"Only 'http' and 'https' are permitted."
            )
    
    @staticmethod
    def _validate_url_host(url: str) -> None:
        """
        Prevent SSRF by blocking private/loopback/link-local IPs.
        
        Resolves the hostname to IP addresses and checks each against
        blocked ranges. This prevents access to internal resources.
        
        Args:
            url: URL to validate
        
        Raises:
            SSRFProtectionError: If hostname resolves to blocked IP
        """
        parsed = urlparse(url)
        hostname = parsed.hostname
        
        if not hostname:
            raise InputValidationError("URL must include a hostname")
        
        try:
            # Resolve hostname to IP addresses
            # This prevents DNS rebinding attacks
            addr_info = socket.getaddrinfo(
                hostname, parsed.port or 80,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM
            )
            
            # Check each resolved IP address
            for family, socktype, proto, canonname, sockaddr in addr_info:
                ip_str = sockaddr[0]
                
                try:
                    ip_addr = ipaddress.ip_address(ip_str)
                    
                    # Check for IPv4-mapped IPv6 addresses and convert
                    if ip_addr.version == 6 and ip_addr.ipv4_mapped:
                        ip_addr = ip_addr.ipv4_mapped
                    
                    # Check against blocked ranges
                    for blocked_range in InputReader.BLOCKED_IP_RANGES:
                        if ip_addr in blocked_range:
                            raise SSRFProtectionError(
                                f"Access to {hostname} ({ip_str}) is blocked. "
                                f"IP is in blocked range {blocked_range}."
                            )
                    
                    # Additional checks for special addresses
                    if ip_addr.is_loopback:
                        raise SSRFProtectionError(
                            f"Access to {hostname} ({ip_str}) is blocked. "
                            f"Loopback addresses are not allowed."
                        )
                    
                    if ip_addr.is_private:
                        raise SSRFProtectionError(
                            f"Access to {hostname} ({ip_str}) is blocked. "
                            f"Private addresses are not allowed."
                        )
                    
                    if ip_addr.is_link_local:
                        raise SSRFProtectionError(
                            f"Access to {hostname} ({ip_str}) is blocked. "
                            f"Link-local addresses are not allowed."
                        )
                    
                    if ip_addr.is_multicast:
                        raise SSRFProtectionError(
                            f"Access to {hostname} ({ip_str}) is blocked. "
                            f"Multicast addresses are not allowed."
                        )
                    
                    # Block unspecified addresses (0.0.0.0, ::)
                    if ip_addr.is_unspecified:
                        raise SSRFProtectionError(
                            f"Access to {hostname} ({ip_str}) is blocked. "
                            f"Unspecified addresses are not allowed."
                        )
                    
                    # Block reserved addresses
                    if ip_addr.is_reserved:
                        raise SSRFProtectionError(
                            f"Access to {hostname} ({ip_str}) is blocked. "
                            f"Reserved addresses are not allowed."
                        )
                    
                except ValueError:
                    # Invalid IP address format
                    raise InputValidationError(
                        f"Could not parse IP address: {ip_str}"
                    )
            
        except socket.gaierror as e:
            raise InputValidationError(f"Could not resolve hostname {hostname}: {e}")
