    def ␎var.name␏(␎
            var.bookend_arg_separator
            ␏self,␎
            var.normal_arg_separator␏other: _Scalar␎var.context_kwarg␏␎
            var.bookend_arg_separator
            ␏) -> ␎var.return_type␏:
        try:
            ␎var.action_statement␏
        except TypeError as exc:
            raise ScalarRequired(other) from exc