from __future__ import annotations

import pathlib
from json import JSONDecodeError
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .chrome import ChromeOptions
from .common import report_from_validation_error
from .logger import LogOptions, logger
from .parser import ParserOptions
from .paths import user_path
from .version import config_version
from .writer import FilterOptions, WriterOptions


class Configuration(BaseModel):
    """Configuration model."""
    model_config = ConfigDict(validate_assignment=True)

    log: LogOptions = Field(default_factory=LogOptions)
    writer: WriterOptions = Field(default_factory=WriterOptions)
    chrome: ChromeOptions = Field(default_factory=ChromeOptions)
    parser: ParserOptions = Field(default_factory=ParserOptions)
    filters: FilterOptions = Field(default_factory=FilterOptions)
    path: Optional[pathlib.Path] = None
    version: str = config_version

    def merge_with(self, other_config: Configuration) -> None:
        """Merge configuration with another one."""
        def assign_attributes(model_source: BaseModel,
                              model_target: BaseModel) -> None:
            """Recursively assign new attributes to existing config."""
            for field in model_source.model_fields_set:
                source_attr = getattr(model_source, field)
                if not isinstance(source_attr, BaseModel):
                    setattr(model_target, field, source_attr)
                else:
                    target_attr = getattr(model_target, field)
                    assert isinstance(target_attr, BaseModel)
                    assign_attributes(source_attr, target_attr)

        assign_attributes(other_config, self)

    def save_config(self) -> None:
        """Save config if it's been loaded from a path previously."""
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, 'w', encoding='utf-8') as f:
                f.write(self.model_dump_json(exclude={'path'}, indent=4))

    @classmethod
    def load_config(cls, config_path: pathlib.Path | None = None,
                    auto_create: bool = True) -> Configuration:
        """Load configuration from path. If path is not specified,
        configuration gets loaded from user's configuration path.
        If errors occurred during loading, method would fallback to
        default configuration.

        Note:
            User configuration path depending on running OS:
            * Unix: ~/.config/parser-2gis/parser-2gis.config
            * Mac: ~/Library/Application Support/parser-2gis/parser-2gis.config
            * Win: C:\\Users\\%USERPROFILE%\\AppData\\Local\\parser-2gis\\parser-2gis.config

        Args:
            config_path: Path to the config file. If not specified, user config gets loaded.
            auto_create: Create config if it does not exist.

        Returns:
            Configuration.
        """
        if not config_path:
            config_path = user_path() / 'parser-2gis.config'

        try:
            if not config_path.is_file():
                if auto_create:
                    config = cls(path=config_path)
                    config.save_config()
                    logger.debug('Создан файл конфигурации: %s', config_path)
                else:
                    config = cls()
            else:
                config = cls.model_validate_json(config_path.read_text(encoding='utf-8'))
                config.path = config_path
        except (JSONDecodeError, ValidationError) as e:
            warning_msg = 'Не удалось загрузить конфигурацию: '
            if isinstance(e, ValidationError):
                errors = []
                errors_report = report_from_validation_error(e)
                for attr_path, error in errors_report.items():
                    error_msg = error['error_message']
                    errors.append(f'атрибут {attr_path} ({error_msg})')

                warning_msg += ', '.join(errors)
            else:
                warning_msg += str(e)

            logger.warning(warning_msg)
            config = cls()

        return config
