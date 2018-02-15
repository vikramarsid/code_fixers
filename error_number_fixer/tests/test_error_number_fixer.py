# coding=utf-8
test_script = """
    self.logger.user_error("This is 1234")
    self.logger.error("This is 1234")
    result.error("This is 1234")
    result.error(234, "This is 234")
    result.error(456, "This is 456")
    """.rstrip() + '\n'