from db.repositories.base import BaseRepository

class TestBatches:
    def test_splits_into_chunks_under_the_parameter_limit(self):
        rows = list(range(2500))
        chunks = list(BaseRepository.batches(rows))
        assert [len(c) for c in chunks] == [1000, 1000, 500]
        assert [x for c in chunks for x in c] == rows

    def test_small_input_is_a_single_chunk(self):
        assert list(BaseRepository.batches([1, 2, 3])) == [[1, 2, 3]]

    def test_empty_input_yields_nothing(self):
        assert list(BaseRepository.batches([])) == []
