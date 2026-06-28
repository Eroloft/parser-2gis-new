from __future__ import annotations

import codecs

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CSVOptions(BaseModel):
    """Represent all possible options for CSV Writer.

    Attributes:
        add_rubrics: Whether to add rubrics to csv or not.
        add_comments: Add comments to complex columns (phones, emails, etc.)
            with extra info, business hours.
        columns_per_entity: Number of columns for a result with multiple possible values.
        remove_empty_columns: Remove empty columns after parsing process finished.
        remove_duplicates: Remove duplicates after parsing process finished.
        join_char: Char for joining complex values.
        clean: Output only essential, human-readable columns (drop schedule,
            postcode, comments, administrative noise and duplicate contact columns).
    """
    model_config = ConfigDict(validate_assignment=True)

    add_rubrics: bool = True
    add_comments: bool = True
    columns_per_entity: int = Field(3, gt=0, le=5)
    remove_empty_columns: bool = True
    remove_duplicates: bool = True
    join_char: str = '; '
    clean: bool = False


class FilterOptions(BaseModel):
    """Record-level filters applied to parsed results (all output formats).

    Attributes:
        dedup_franchises: Keep a single branch per organization (drop franchise duplicates).
        require_phone: Keep only records that have a phone number.
        require_whatsapp: Keep only records reachable via WhatsApp.
        require_social: Keep only records with at least one social network / messenger.
        require_email: Keep only records that have an e-mail.
        require_website: Keep only records that have a website.
        min_rating: Keep only records with rating >= this value (0 disables).
        min_reviews: Keep only records with review count >= this value (0 disables).
    """
    model_config = ConfigDict(validate_assignment=True)

    dedup_franchises: bool = False
    require_phone: bool = False
    require_whatsapp: bool = False
    require_social: bool = False
    require_email: bool = False
    require_website: bool = False
    min_rating: float = Field(0.0, ge=0, le=5)
    min_reviews: int = Field(0, ge=0)


class WriterOptions(BaseModel):
    """Represent all possible options for File Writer.

    Attributes:
       encoding: Encoding of output document.
       verbose: Echo to stdout parsing item's name.
    """
    model_config = ConfigDict(validate_assignment=True)

    encoding: str = 'utf-8-sig'
    verbose: bool = True
    csv: CSVOptions = Field(default_factory=CSVOptions)

    @field_validator('encoding')
    @classmethod
    def encoding_exists(cls, v: str) -> str:
        """Determine if `encoding` exists."""
        try:
            codecs.lookup(v)
        except LookupError:
            raise ValueError
        return v
