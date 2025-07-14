    def ␎var.name␏(␎
            var.bookend_arg_separator
            ␏self,␎
            var.normal_arg_separator␏other: Money␎var.context_kwarg␏␎
            var.bookend_arg_separator
            ␏) -> ␎var.return_type␏:
        try:
            if self.currency != other.currency:
                raise MismatchedCurrency(self.currency, other.currency)

            ␎var.action_statement␏

        except AttributeError as exc:
            raise MoneyRequired(other) from exc