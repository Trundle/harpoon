from harpoon.bot.hipchat import _create_command_matcher


class TestCommandMatcher(object):
    MATCHER = _create_command_matcher()

    def test_without_spaces(self):
        result = self.MATCHER("-->container")
        assert result
        assert result.groups() == ("-->", "container")

    def test_no_container_does_not_match(self):
        result = self.MATCHER("-->")
        assert not result

    def test_with_spaces(self):
        result = self.MATCHER("--> container")
        assert result
        assert result.groups() == ("-->", " container")

    def test_alias_with_spaces(self):
        result = self.MATCHER("harpoon container")
        assert result
        assert result.groups() == ("harpoon", " container")