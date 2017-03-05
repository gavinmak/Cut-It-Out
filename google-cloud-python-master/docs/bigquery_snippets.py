# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Testable usage examples for Google BigQuery API wrapper

Each example function takes a ``client`` argument (which must be an instance
of :class:`google.cloud.bigquery.client.Client`) and uses it to perform a task
with the API.

To facilitate running the examples as system tests, each example is also passed
a ``to_delete`` list;  the function adds to the list any objects created which
need to be deleted during teardown.
"""

import operator
import time

import six

from google.cloud.bigquery import SchemaField
from google.cloud.bigquery.client import Client

ORIGINAL_FRIENDLY_NAME = 'Original friendly name'
ORIGINAL_DESCRIPTION = 'Original description'
LOCALLY_CHANGED_FRIENDLY_NAME = 'Locally-changed friendly name'
LOCALLY_CHANGED_DESCRIPTION = 'Locally-changed description'
PATCHED_FRIENDLY_NAME = 'Patched friendly name'
PATCHED_DESCRIPTION = 'Patched description'
UPDATED_FRIENDLY_NAME = 'Updated friendly name'
UPDATED_DESCRIPTION = 'Updated description'

SCHEMA = [
    SchemaField('full_name', 'STRING', mode='required'),
    SchemaField('age', 'INTEGER', mode='required'),
]

QUERY = (
    'SELECT name FROM [bigquery-public-data:usa_names.usa_1910_2013] '
    'WHERE state = "TX"')


def snippet(func):
    """Mark ``func`` as a snippet example function."""
    func._snippet = True
    return func


def _millis():
    return time.time() * 1000


class _CloseOnDelete(object):

    def __init__(self, wrapped):
        self._wrapped = wrapped

    def delete(self):
        self._wrapped.close()


@snippet
def client_list_datasets(client, _):
    """List datasets for a project."""

    def do_something_with(_):
        pass

    # [START client_list_datasets]
    for dataset in client.list_datasets():  # API request(s)
        do_something_with(dataset)
    # [END client_list_datasets]


@snippet
def dataset_create(client, to_delete):
    """Create a dataset."""
    DATASET_NAME = 'dataset_create_%d' % (_millis(),)

    # [START dataset_create]
    dataset = client.dataset(DATASET_NAME)
    dataset.create()              # API request
    # [END dataset_create]

    to_delete.append(dataset)


@snippet
def dataset_exists(client, to_delete):
    """Test existence of a dataset."""
    DATASET_NAME = 'dataset_exists_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    to_delete.append(dataset)

    # [START dataset_exists]
    assert not dataset.exists()   # API request
    dataset.create()              # API request
    assert dataset.exists()       # API request
    # [END dataset_exists]


@snippet
def dataset_reload(client, to_delete):
    """Reload a dataset's metadata."""
    DATASET_NAME = 'dataset_reload_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.description = ORIGINAL_DESCRIPTION
    dataset.create()
    to_delete.append(dataset)

    # [START dataset_reload]
    assert dataset.description == ORIGINAL_DESCRIPTION
    dataset.description = LOCALLY_CHANGED_DESCRIPTION
    assert dataset.description == LOCALLY_CHANGED_DESCRIPTION
    dataset.reload()              # API request
    assert dataset.description == ORIGINAL_DESCRIPTION
    # [END dataset_reload]


@snippet
def dataset_patch(client, to_delete):
    """Patch a dataset's metadata."""
    DATASET_NAME = 'dataset_patch_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.description = ORIGINAL_DESCRIPTION
    dataset.create()
    to_delete.append(dataset)

    # [START dataset_patch]
    ONE_DAY_MS = 24 * 60 * 60 * 1000
    assert dataset.description == ORIGINAL_DESCRIPTION
    dataset.patch(
        description=PATCHED_DESCRIPTION,
        default_table_expiration_ms=ONE_DAY_MS
    )      # API request
    assert dataset.description == PATCHED_DESCRIPTION
    assert dataset.default_table_expiration_ms == ONE_DAY_MS
    # [END dataset_patch]


@snippet
def dataset_update(client, to_delete):
    """Update a dataset's metadata."""
    DATASET_NAME = 'dataset_update_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.description = ORIGINAL_DESCRIPTION
    dataset.create()
    to_delete.append(dataset)
    dataset.reload()

    # [START dataset_update]
    from google.cloud.bigquery import AccessGrant
    assert dataset.description == ORIGINAL_DESCRIPTION
    assert dataset.default_table_expiration_ms is None
    grant = AccessGrant(
        role='READER', entity_type='domain', entity_id='example.com')
    assert grant not in dataset.access_grants
    ONE_DAY_MS = 24 * 60 * 60 * 1000
    dataset.description = UPDATED_DESCRIPTION
    dataset.default_table_expiration_ms = ONE_DAY_MS
    grants = list(dataset.access_grants)
    grants.append(grant)
    dataset.access_grants = grants
    dataset.update()              # API request
    assert dataset.description == UPDATED_DESCRIPTION
    assert dataset.default_table_expiration_ms == ONE_DAY_MS
    assert grant in dataset.access_grants
    # [END dataset_update]


@snippet
def dataset_delete(client, _):
    """Delete a dataset."""
    DATASET_NAME = 'dataset_delete_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()

    # [START dataset_delete]
    assert dataset.exists()       # API request
    dataset.delete()
    assert not dataset.exists()   # API request
    # [END dataset_delete]


@snippet
def dataset_list_tables(client, to_delete):
    """List tables within a dataset."""
    DATASET_NAME = 'dataset_list_tables_dataset_%d' % (_millis(),)
    TABLE_NAME = 'dataset_list_tables_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()
    to_delete.append(dataset)

    # [START dataset_list_tables]
    tables = list(dataset.list_tables())  # API request(s)
    assert len(tables) == 0
    table = dataset.table(TABLE_NAME)
    table.view_query = QUERY
    table.create()                          # API request
    tables = list(dataset.list_tables())  # API request(s)
    assert len(tables) == 1
    assert tables[0].name == TABLE_NAME
    # [END dataset_list_tables]
    to_delete.insert(0, table)


@snippet
def table_create(client, to_delete):
    """Create a table."""
    DATASET_NAME = 'table_create_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_create_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()
    to_delete.append(dataset)

    # [START table_create]
    table = dataset.table(TABLE_NAME, SCHEMA)
    table.create()                          # API request
    # [END table_create]

    to_delete.insert(0, table)


@snippet
def table_exists(client, to_delete):
    """Test existence of a table."""
    DATASET_NAME = 'table_exists_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_exists_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()
    to_delete.append(dataset)

    # [START table_exists]
    table = dataset.table(TABLE_NAME, SCHEMA)
    assert not table.exists()               # API request
    table.create()                          # API request
    assert table.exists()                   # API request
    # [END table_exists]

    to_delete.insert(0, table)


@snippet
def table_reload(client, to_delete):
    """Reload a table's metadata."""
    DATASET_NAME = 'table_reload_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_reload_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()
    to_delete.append(dataset)

    table = dataset.table(TABLE_NAME, SCHEMA)
    table.friendly_name = ORIGINAL_FRIENDLY_NAME
    table.description = ORIGINAL_DESCRIPTION
    table.create()
    to_delete.insert(0, table)

    # [START table_reload]
    assert table.friendly_name == ORIGINAL_FRIENDLY_NAME
    assert table.description == ORIGINAL_DESCRIPTION
    table.friendly_name = LOCALLY_CHANGED_FRIENDLY_NAME
    table.description = LOCALLY_CHANGED_DESCRIPTION
    table.reload()                  # API request
    assert table.friendly_name == ORIGINAL_FRIENDLY_NAME
    assert table.description == ORIGINAL_DESCRIPTION
    # [END table_reload]


@snippet
def table_patch(client, to_delete):
    """Patch a table's metadata."""
    DATASET_NAME = 'table_patch_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_patch_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.description = ORIGINAL_DESCRIPTION
    dataset.create()
    to_delete.append(dataset)

    table = dataset.table(TABLE_NAME, SCHEMA)
    table.friendly_name = ORIGINAL_FRIENDLY_NAME
    table.description = ORIGINAL_DESCRIPTION
    table.create()
    to_delete.insert(0, table)

    # [START table_patch]
    assert table.friendly_name == ORIGINAL_FRIENDLY_NAME
    assert table.description == ORIGINAL_DESCRIPTION
    table.patch(
        friendly_name=PATCHED_FRIENDLY_NAME,
        description=PATCHED_DESCRIPTION,
    )      # API request
    assert table.friendly_name == PATCHED_FRIENDLY_NAME
    assert table.description == PATCHED_DESCRIPTION
    # [END table_patch]


@snippet
def table_update(client, to_delete):
    """Update a table's metadata."""
    DATASET_NAME = 'table_update_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_update_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.description = ORIGINAL_DESCRIPTION
    dataset.create()
    to_delete.append(dataset)

    table = dataset.table(TABLE_NAME, SCHEMA)
    table.friendly_name = ORIGINAL_FRIENDLY_NAME
    table.description = ORIGINAL_DESCRIPTION
    table.create()
    to_delete.insert(0, table)

    # [START table_update]
    assert table.friendly_name == ORIGINAL_FRIENDLY_NAME
    assert table.description == ORIGINAL_DESCRIPTION
    NEW_SCHEMA = table.schema[:]
    NEW_SCHEMA.append(SchemaField('phone', 'string'))
    table.friendly_name = UPDATED_FRIENDLY_NAME
    table.description = UPDATED_DESCRIPTION
    table.schema = NEW_SCHEMA
    table.update()              # API request
    assert table.friendly_name == UPDATED_FRIENDLY_NAME
    assert table.description == UPDATED_DESCRIPTION
    assert table.schema == NEW_SCHEMA
    # [END table_update]


def _warm_up_inserted_table_data(table):
    # Allow for 90 seconds of "warm up" before rows visible.  See:
    # https://cloud.google.com/bigquery/streaming-data-into-bigquery#dataavailability
    rows = ()
    counter = 18

    while len(rows) == 0 and counter > 0:
        counter -= 1
        iterator = table.fetch_data()
        page = six.next(iterator.pages)
        rows = list(page)
        if len(rows) == 0:
            time.sleep(5)


@snippet
def table_insert_fetch_data(client, to_delete):
    """Insert / fetch table data."""
    DATASET_NAME = 'table_insert_fetch_data_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_insert_fetch_data_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()
    to_delete.append(dataset)

    table = dataset.table(TABLE_NAME, SCHEMA)
    table.create()
    to_delete.insert(0, table)

    # [START table_insert_data]
    ROWS_TO_INSERT = [
        (u'Phred Phlyntstone', 32),
        (u'Wylma Phlyntstone', 29),
    ]

    table.insert_data(ROWS_TO_INSERT)
    # [END table_insert_data]

    _warm_up_inserted_table_data(table)

    found_rows = []

    def do_something(row):
        found_rows.append(row)

    # [START table_fetch_data]
    for row in table.fetch_data():
        do_something(row)
    # [END table_fetch_data]

    assert len(found_rows) == len(ROWS_TO_INSERT)
    by_age = operator.itemgetter(1)
    found_rows = reversed(sorted(found_rows, key=by_age))
    for found, to_insert in zip(found_rows, ROWS_TO_INSERT):
        assert found == to_insert


@snippet
def table_upload_from_file(client, to_delete):
    """Upload table data from a CSV file."""
    import csv
    import tempfile
    DATASET_NAME = 'table_upload_from_file_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_upload_from_file_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()
    to_delete.append(dataset)

    table = dataset.table(TABLE_NAME, SCHEMA)
    table.create()
    to_delete.insert(0, table)

    csv_file = tempfile.NamedTemporaryFile(suffix='.csv')
    to_delete.append(_CloseOnDelete(csv_file))

    # [START table_upload_from_file]
    writer = csv.writer(csv_file)
    writer.writerow((b'full_name', b'age'))
    writer.writerow((b'Phred Phlyntstone', b'32'))
    writer.writerow((b'Wylma Phlyntstone', b'29'))
    csv_file.flush()

    with open(csv_file.name, 'rb') as readable:
        table.upload_from_file(
            readable, source_format='CSV', skip_leading_rows=1)
    # [END table_upload_from_file]

    _warm_up_inserted_table_data(table)

    iterator = table.fetch_data()
    page = six.next(iterator.pages)
    rows = list(page)
    total = iterator.total_rows
    token = iterator.next_page_token

    assert len(rows) == total == 2
    assert token is None
    assert rows[0] == (u'Phred Phlyntstone', 32)
    assert rows[1] == (u'Wylma Phlyntstone', 29)


@snippet
def table_delete(client, to_delete):
    """Delete a table."""
    DATASET_NAME = 'table_delete_dataset_%d' % (_millis(),)
    TABLE_NAME = 'table_create_table_%d' % (_millis(),)
    dataset = client.dataset(DATASET_NAME)
    dataset.create()
    to_delete.append(dataset)

    table = dataset.table(TABLE_NAME, SCHEMA)
    table.create()

    # [START table_delete]
    assert table.exists()       # API request
    table.delete()              # API request
    assert not table.exists()   # API request
    # [END table_delete]


@snippet
def client_list_jobs(client, _):
    """List jobs for a project."""

    def do_something_with(_):
        pass

    # [START client_list_jobs]
    job_iterator = client.list_jobs()
    for job in job_iterator:   # API request(s)
        do_something_with(job)
    # [END client_list_jobs]


@snippet
def client_run_sync_query(client, _):
    """Run a synchronous query."""
    LIMIT = 100
    LIMITED = '%s LIMIT %d' % (QUERY, LIMIT)
    TIMEOUT_MS = 1000

    # [START client_run_sync_query]
    query = client.run_sync_query(LIMITED)
    query.timeout_ms = TIMEOUT_MS
    query.run()             # API request

    assert query.complete
    assert len(query.rows) == LIMIT
    assert [field.name for field in query.schema] == ['name']
    # [END client_run_sync_query]


@snippet
def client_run_sync_query_w_param(client, _):
    """Run a synchronous query using a query parameter"""
    QUERY_W_PARAM = (
        'SELECT name FROM `bigquery-public-data.usa_names.usa_1910_2013` '
        'WHERE state = @state')
    LIMIT = 100
    LIMITED = '%s LIMIT %d' % (QUERY_W_PARAM, LIMIT)
    TIMEOUT_MS = 1000

    # [START client_run_sync_query_w_param]
    from google.cloud.bigquery import ScalarQueryParameter
    param = ScalarQueryParameter('state', 'STRING', 'TX')
    query = client.run_sync_query(LIMITED, query_parameters=[param])
    query.use_legacy_sql = False
    query.timeout_ms = TIMEOUT_MS
    query.run()             # API request

    assert query.complete
    assert len(query.rows) == LIMIT
    assert [field.name for field in query.schema] == ['name']
    # [END client_run_sync_query_w_param]


@snippet
def client_run_sync_query_paged(client, _):
    """Run a synchronous query with paged results."""
    TIMEOUT_MS = 1000
    PAGE_SIZE = 100
    LIMIT = 1000
    LIMITED = '%s LIMIT %d' % (QUERY, LIMIT)

    all_rows = []

    def do_something_with(rows):
        all_rows.extend(rows)

    # [START client_run_sync_query_paged]
    query = client.run_sync_query(LIMITED)
    query.timeout_ms = TIMEOUT_MS
    query.max_results = PAGE_SIZE
    query.run()                     # API request

    assert query.complete
    assert query.page_token is not None
    assert len(query.rows) == PAGE_SIZE
    assert [field.name for field in query.schema] == ['name']

    rows = query.rows
    token = query.page_token

    while True:
        do_something_with(rows)
        if token is None:
            break
        rows, total_count, token = query.fetch_data(
            page_token=token)       # API request
    # [END client_run_sync_query_paged]

    assert total_count == LIMIT
    assert len(all_rows) == LIMIT


@snippet
def client_run_sync_query_timeout(client, _):
    """Run a synchronous query w/ timeout"""
    TIMEOUT_MS = 10

    all_rows = []

    def do_something_with(rows):
        all_rows.extend(rows)

    # [START client_run_sync_query_timeout]
    query = client.run_sync_query(QUERY)
    query.timeout_ms = TIMEOUT_MS
    query.use_query_cache = False
    query.run()                           # API request

    assert not query.complete

    job = query.job
    job.reload()                          # API rquest
    retry_count = 0

    while retry_count < 10 and job.state != u'DONE':
        time.sleep(1.5**retry_count)      # exponential backoff
        retry_count += 1
        job.reload()                      # API request

    assert job.state == u'DONE'

    rows, total_count, token = query.fetch_data()  # API request
    while True:
        do_something_with(rows)
        if token is None:
            break
        rows, total_count, token = query.fetch_data(
            page_token=token)  # API request
    # [END client_run_sync_query_timeout]

    assert len(all_rows) == total_count


def _find_examples():
    funcs = [obj for obj in globals().values()
             if getattr(obj, '_snippet', False)]
    for func in sorted(funcs, key=lambda f: f.func_code.co_firstlineno):
        yield func


def main():
    client = Client()
    for example in _find_examples():
        to_delete = []
        print('%-30s: %s' % (
            example.func_name, example.func_doc))
        try:
            example(client, to_delete)
        except AssertionError as e:
            print('   FAIL: %s' % (e,))
        except Exception as e:  # pylint: disable=broad-except
            print('  ERROR: %r' % (e,))
        for item in to_delete:
            item.delete()


if __name__ == '__main__':
    main()
