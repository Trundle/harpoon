from harpoon.docker import _create_image_matcher


class TestImageMatcher(object):
    def test_image_without_registry_and_tag(self):
        matcher = _create_image_matcher("spam")
        assert matcher("spam")
        assert not matcher("spamsuffix")
        assert not matcher("prefixspam")

    def test_image_with_tag_and_without_registry(self):
        matcher = _create_image_matcher("spam")
        assert matcher("spam:42")
        assert not matcher("spamsuffix:42")
        assert not matcher("prefixspam:42")

    def test_image_with_registry_and_tag(self):
        matcher = _create_image_matcher("spam")
        assert matcher("hub.example.com/spam:42")
        assert not matcher("hub.example.com/spamsuffix:42")
        assert not matcher("hub.example.com/prefixspam:42")
