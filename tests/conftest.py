"""Pytest configuration and fixture setup.

Provides compatibility patching for mongomock when running against newer PyMongo
versions (e.g. PyMongo 4.19+ which passes 'sort' into BulkOperationBuilder.add_update).
"""

import mongomock

# Patch mongomock BulkOperationBuilder.add_update to accept 'sort' without raising TypeError
_orig_add_update = mongomock.collection.BulkOperationBuilder.add_update


def _compatible_add_update(
    self,
    filter,
    doc,
    multi,
    upsert,
    collation=None,
    array_filters=None,
    hint=None,
    sort=None,
    **kwargs,
):
    return _orig_add_update(
        self,
        filter,
        doc,
        multi,
        upsert,
        collation=collation,
        array_filters=array_filters,
        hint=hint,
    )


mongomock.collection.BulkOperationBuilder.add_update = _compatible_add_update
