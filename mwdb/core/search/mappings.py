import re
from typing import Any, Dict, List, Tuple, Type

from luqum.tree import Term

from mwdb.model import Comment, Config, File, Object, Tag, TextBlob

from .exceptions import FieldNotQueryableException, MultipleObjectsQueryException
from .fields import (
    AttributeField,
    BaseField,
    DatetimeField,
    FavoritesField,
    JSONField,
    ListField,
    RelationField,
    ShareField,
    SizeField,
    StringField,
    UploaderField,
)

object_mapping: Dict[str, Type[Object]] = {
    "file": File,
    "object": Object,
    "static": Config,
    "config": Config,
    "blob": TextBlob,
}

field_mapping: Dict[str, Dict[str, BaseField]] = {
    Object.__name__: {
        "dhash": StringField(Object.dhash),
        "tag": ListField(Object.tags, Tag.tag),
        "comment": ListField(Object.comments, Comment.comment),
        "meta": AttributeField(Object.meta),
        "shared": ShareField(Object.shares),
        "uploader": UploaderField(Object.related_shares),
        "upload_time": DatetimeField(Object.upload_time),
        "parent": RelationField(Object.parents),
        "child": RelationField(Object.children),
        "favorites": FavoritesField(Object.followers),
    },
    File.__name__: {
        "name": StringField(File.file_name),
        "size": SizeField(File.file_size),
        "type": StringField(File.file_type),
        "md5": StringField(File.md5),
        "sha1": StringField(File.sha1),
        "sha256": StringField(File.sha256),
        "sha512": StringField(File.sha512),
        "ssdeep": StringField(File.ssdeep),
        "crc32": StringField(File.crc32),
    },
    Config.__name__: {
        "type": StringField(Config.config_type),
        "family": StringField(Config.family),
        "cfg": JSONField(Config.cfg),
    },
    TextBlob.__name__: {
        "name": StringField(TextBlob.blob_name),
        "size": SizeField(TextBlob.blob_size),
        "type": StringField(TextBlob.blob_type),
        "content": StringField(TextBlob._content),
        "first_seen": DatetimeField(TextBlob.upload_time),
        "last_seen": DatetimeField(TextBlob.last_seen),
    },
}


def get_default_field_condition(queried_type: Type[Object], term: Term) -> Any:
    if queried_type is File:
        if re.match(r"^[0-9a-fA-F]{8}$", term.unescaped_value):
            return StringField(File.crc32).get_condition(term, [])
        elif re.match(r"^[0-9a-fA-F]{32}$", term.unescaped_value):
            return StringField(File.md5).get_condition(term, [])
        elif re.match(r"^[0-9a-fA-F]{40}$", term.unescaped_value):
            return StringField(File.sha1).get_condition(term, [])
        elif re.match(r"^[0-9a-fA-F]{64}$", term.unescaped_value):
            return StringField(File.sha256).get_condition(term, [])
        elif re.match(r"^[0-9a-fA-F]{128}$", term.unescaped_value):
            return StringField(File.sha512).get_condition(term, [])
    elif queried_type is Config:
        wildcarded_term = Term(value=f"*{term.value}*")
        return JSONField(Config.cfg).get_condition(wildcarded_term, [])
    elif queried_type is TextBlob:
        wildcarded_term = Term(value=f"*{term.value}*")
        return StringField(TextBlob._content).get_condition(wildcarded_term, [])
    return None


def get_field_mapper(
    queried_type: Type[Object], field_selector: str
) -> Tuple[BaseField, List[str]]:
    field_path = field_selector.split(".")

    # Map object type selector
    if field_path[0] in object_mapping:
        selected_type = object_mapping[field_path[0]]
        # Because object type selector determines queried type, we can't use specialized
        # fields from different types in the same query
        if not issubclass(selected_type, queried_type):
            raise MultipleObjectsQueryException(
                f"Can't search for objects with type '{selected_type.__name__}' "
                f"and '{queried_type.__name__}' in the same query"
            )
        field_path = field_path[1:]
    else:
        selected_type = queried_type

    # If there was only object type selector: raise exception
    if not field_path:
        raise FieldNotQueryableException(f"No such field: {field_selector}")

    # Map object field selector
    if field_path[0] in field_mapping[selected_type.__name__]:
        field = field_mapping[selected_type.__name__][field_path[0]]
    elif field_path[0] in field_mapping[Object.__name__]:
        field = field_mapping[Object.__name__][field_path[0]]
    else:
        raise FieldNotQueryableException(f"No such field: {field_selector}")
    return field, field_path[1:]
