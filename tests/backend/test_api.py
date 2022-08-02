import pytest
import requests
from dateutil.parser import parse

from .utils import MwdbTest, rand_string


@pytest.fixture(scope="session", autouse=True)
def check_operational(request):
    test = MwdbTest()
    test.check_operational()


def test_login():
    test = MwdbTest()
    res = test.login()
    assert 'token' in res and res['login'] == 'admin'


def test_add_sample():
    test = MwdbTest()
    test.login()

    filename = 'filename'
    file_content = 'content'

    res = test.add_sample(filename, file_content)

    assert res['file_name'] == filename
    assert res['file_size'] == len(file_content)
    assert res['parents'] == []
    assert res['children'] == []
    assert res['tags'] == []
    parse(res['upload_time'])


def test_add_sample_legacy():
    test = MwdbTest()
    test.login()

    filename = 'filename'
    file_content = 'content'

    res = test.add_sample_legacy(filename, file_content)

    assert res['file_name'] == filename
    assert res['file_size'] == len(file_content)
    assert res['parents'] == []
    assert res['children'] == []
    assert res['tags'] == []
    parse(res['upload_time'])


def test_get_sample():
    test = MwdbTest()
    test.login()

    filename = 'filename'
    file_content = 'content'

    sample = test.add_sample(filename, file_content)
    res = test.get_sample(sample['id'])

    assert res['file_name'] == filename
    assert res['file_size'] == len(file_content)
    assert res['parents'] == []
    assert res['children'] == []
    assert res['tags'] == []
    parse(res['upload_time'])


def test_search():
    test = MwdbTest()
    test.login()

    filename = 'filename'
    file_content = 'content'

    sample = test.add_sample(filename, file_content)
    allowed_names = [
        sample['id'], sample['md5'], sample['sha1'],
        sample['sha256'], sample['sha256'].upper()
    ]

    for name in allowed_names:
        res = test.get_sample(name)
        assert res['id'] == sample['id']
        assert res['file_name'] == filename
        assert res['file_size'] == len(file_content)
        assert res['parents'] == []
        assert res['children'] == []
        assert res['tags'] == []
        parse(res['upload_time'])


@pytest.mark.parametrize('num_parents,num_children', [
    (1, 1),
    (1, 2),
    (2, 1),
    (2, 2)
])
def test_relations(num_parents, num_children):
    test = MwdbTest()
    test.login()

    parents_id = set()
    children_id = set()

    for _ in range(num_parents):
        parent = test.add_sample()
        parents_id.add(parent['id'])

    for _ in range(num_children):
        content = rand_string()
        for p_hash in parents_id:
            child_res = test.add_sample(content, content, p_hash)
            children_id.add(child_res['id'])

    for p_hash in parents_id:
        parent = test.get_sample(p_hash)
        assert len(parent['children']) == num_children
        for c in children_id:
            assert c in [x['id'] for x in parent['children']]

    for c_hash in children_id:
        child = test.get_sample(c_hash)
        assert len(child['parents']) == num_parents
        for p in parents_id:
            assert p in [x['id'] for x in child['parents']]


def test_add_tags():
    test = MwdbTest()
    test.login()

    sample = test.add_sample()

    tags_expected = [rand_string() for _ in range(4)]
    for tag in tags_expected:
        test.add_tag(sample['id'], tag)

    tags_response = test.get_tags(sample['id'])
    tags_returned = [t['tag'] for t in tags_response]

    assert len(tags_returned) == len(tags_expected)
    assert all(t in tags_returned for t in tags_expected)


def test_delete_tags():
    tag1 = 'tag1'
    tag2 = 'tag2'

    test = MwdbTest()
    test.login()

    sample = test.add_sample()
    identifier = sample['id']
    test.add_tag(identifier, tag1)
    test.add_tag(identifier, tag2)
    test.delete_tag(identifier, tag1)

    tags = test.get_tags(identifier)
    assert len(tags) == 1
    assert tags[0]['tag'] == tag2


@pytest.mark.parametrize('num_comments', [
    0,
    1,
    5
])
def test_comment(num_comments):
    expected_comments = [rand_string() for _ in range(num_comments)]

    test = MwdbTest()
    test.login()

    sample = test.add_sample()
    identifier = sample['id']

    for c in expected_comments:
        test.add_comment(identifier, c)

    comments = test.get_comments(identifier)
    assert len(comments) == num_comments
    assert all(c['comment'] in expected_comments for c in comments)


def test_download_sample():
    test = MwdbTest()
    test.login()

    expected = rand_string()
    sample = test.add_sample(content=expected)

    downloaded = test.download_file(sample['id'])
    assert downloaded.decode() == expected


def test_download_sample_with_token():
    test = MwdbTest()
    test.login()

    expected = rand_string()
    sample = test.add_sample(content=expected)

    token = test.get_download_token(sample['id'])
    r = requests.get(
        f'{test.mwdb_url}/file/{sample["id"]}/download',
        params={"token": token},
    )

    r.raise_for_status()
    downloaded = r.text

    assert downloaded == expected
