"""
Module: Data Loader
Universal CSV, Excel (.xlsx, .xls) data loader with multi-encoding fallback,
delimiter sniffing, worksheet selection, and header sanitization.
"""
import io
import os
import logging
from typing import Tuple, Optional, List, Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

class DataLoader:
    SUPPORTED_EXTS = [".csv", ".xlsx", ".xls"]

    @staticmethod
    def inspect_file(uploaded_file) -> Dict[str, Any]:
        """Inspects uploaded file metadata."""
        file_name = uploaded_file.name
        file_ext = os.path.splitext(file_name)[1].lower()
        file_size_bytes = uploaded_file.size if hasattr(uploaded_file, "size") else len(uploaded_file.getvalue())
        return {
            "name": file_name,
            "extension": file_ext,
            "size_bytes": file_size_bytes,
            "size_kb": round(file_size_bytes / 1024, 2),
            "size_mb": round(file_size_bytes / (1024 * 1024), 2),
            "supported": file_ext in DataLoader.SUPPORTED_EXTS
        }

    @staticmethod
    def get_excel_sheets(file_bytes: bytes) -> List[str]:
        """Returns sheet names from Excel bytes."""
        try:
            excel = pd.ExcelFile(io.BytesIO(file_bytes))
            return excel.sheet_names
        except Exception as e:
            logger.error(f"Failed to read Excel sheets: {e}")
            return []

    @staticmethod
    def load_dataset(
        file_bytes: bytes,
        file_name: str,
        sheet_name: Optional[str] = None,
        delimiter: Optional[str] = None
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Parses CSV/Excel file bytes into a sanitized pandas DataFrame.
        Returns (DataFrame, error_message).
        """
        if not file_bytes or len(file_bytes) == 0:
            return None, "The uploaded file is empty (0 bytes)."

        ext = os.path.splitext(file_name)[1].lower()
        if ext not in DataLoader.SUPPORTED_EXTS:
            return None, f"Unsupported file extension '{ext}'. Please upload CSV or Excel files."

        try:
            if ext == ".csv":
                encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
                df = None
                last_err = None
                for enc in encodings:
                    try:
                        kwargs = {}
                        if delimiter and delimiter != "Auto":
                            kwargs["sep"] = delimiter
                        else:
                            kwargs["sep"] = None
                            kwargs["engine"] = "python"

                        df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc, **kwargs)
                        break
                    except Exception as e:
                        last_err = e
                        continue

                if df is None:
                    return None, f"Failed to parse CSV: {str(last_err)}"

            elif ext in [".xlsx", ".xls"]:
                kwargs = {}
                if sheet_name:
                    kwargs["sheet_name"] = sheet_name
                df = pd.read_excel(io.BytesIO(file_bytes), **kwargs)

            if df is None or df.empty:
                return df, "Warning: The parsed dataset has 0 rows."

            # Clean and sanitize column names
            clean_cols = []
            seen = {}
            for i, col in enumerate(df.columns):
                c_str = str(col).strip()
                if not c_str:
                    c_str = f"Unnamed_Col_{i}"
                if c_str in seen:
                    seen[c_str] += 1
                    c_str = f"{c_str}_{seen[c_str]}"
                else:
                    seen[c_str] = 0
                clean_cols.append(c_str)
            df.columns = clean_cols

            return df, None

        except Exception as e:
            logger.exception("Error during dataset ingestion")
            return None, f"Error processing file: {str(e)}"

