    @overload
    def ␎var.name␏(␎
            var.bookend_arg_separator
            ␏self,␎
            var.normal_arg_separator␏other: Money␎
            var.context_kwarg␏␎
            var.bookend_arg_separator
            ␏) -> ␎var.return1␏: ...
    @overload
    def ␎var.name␏(␎
            var.bookend_arg_separator
            ␏self,␎
            var.normal_arg_separator␏other: _Scalar␎
            var.context_kwarg␏␎
            var.bookend_arg_separator
            ␏) -> Money: ...
    def ␎var.name␏(␎
            var.bookend_arg_separator
            ␏self,␎
            var.normal_arg_separator␏other: Money | _Scalar␎
            var.context_kwarg␏␎
            var.bookend_arg_separator
            ␏) -> ␎var.return3␏:
        if isinstance(other, Money):
            if self.currency != other.currency:
                raise MismatchedCurrency(self.currency, other.currency)

            return ␎var.actiontype_start␏self.amount.␎var.passthrough_name␏(␎var.linebreaker␏other.amount␎var.context_passthrough␏)␎var.actiontype_end␏

        else:
            return self.currency.mint(␎var.linebreaker␏self.amount.␎var.passthrough_name␏(other␎var.context_passthrough␏))