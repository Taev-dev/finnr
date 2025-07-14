"""I was on the fence about whether or not to codegen this.

At the end of the day, this definitely, positively did NOT save time on
the first iteration. But I genuinely think it will be easier to maintain
and significantly less error-prone (copypastas are a great way to create
typos!) than the alternative IN THE LONG RUN. Right now, with templatey
how it is... the indentation just really throws a wrench in the works.

Plus, we already need codegen for the ISO module, so... in for a penny,
in for a pound.

The other advantage of this approach is that we can use the _MethodInfo
class as a way of validating what little copypasta / manual data entry
is unavoidable, which provides some added reassurance we didn't mess
things up.

Also, one further advantage is that the money math code is MASSIVE.
There's just a TON of very repetitive code, and separating that out
into a dedicated module ^^just for the math^^ makes the actual Money
object much easier to read.

That all being said, this is anything but expressive. I think there's
still MAJOR work to be done in templatey before the templates read
like normal python files. By far the biggest issue here is indentation;
I suppose another workaround would be to just suppress line length
limitations. :shrug:

The other thing that could make a world of difference is if I had a way
to auto-format the code AFTER codegen, using our preferred style guide.
That might be the most ideal way of doing things, since it would save
us from needing to "encode" the style guide in the form of templatey
templates.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import cast

from templatey import RenderEnvironment
from templatey.prebaked.loaders import CompanionFileLoader

from finnr_codegen._types import REPO_ROOT
from finnr_codegen.templates import BinaryMethodReqMoneyTemplate
from finnr_codegen.templates import BinaryMethodReqScalarTemplate
from finnr_codegen.templates import MoneymathModuleTemplate
from finnr_codegen.templates import OverloadedMethodTemplate
from finnr_codegen.templates import UnaryMethodTemplate

templatey_loader = CompanionFileLoader()
templatey_env = RenderEnvironment(
    env_functions=(),
    template_loader=templatey_loader)


def codegen_moneymath_module():  # noqa: PLR0912
    dest_path = REPO_ROOT / 'src_py/finnr/_moneymath.py'
    methods = []

    for method_info in MATH_METHODS_TO_CODEGEN:
        context_kwarg = _ContextKwarg(
            method_info.has_context, method_info.requires_long_signature)
        context_passthrough = _ContextPassthrough(
            method_info.has_context, method_info.is_unary)

        if method_info.is_unary:
            if method_info.return_type is _Type.MONEY:
                passthrough = (
                    'self.currency.mint(self.amount.'
                    + method_info.passthrough_name
                    + f'({context_passthrough}))')

            else:
                passthrough = (
                    f'self.amount.{method_info.passthrough_name}'
                    + f'({context_passthrough})')

            # Note: unary is never augmented
            action_statement = f'return {passthrough}'
            methods.append(UnaryMethodTemplate(
                name=method_info.name,
                action_statement=action_statement,
                # Cannot be overloaded for unary
                return_type=cast(str, method_info.return_type.value),
                context_kwarg=context_kwarg))

        elif method_info.is_overloaded:
            linebreaker = _LineBreaker(
                do_linebreak=method_info.requires_long_signature,
                indent_level=4)
            if method_info.return_type is _Type.OVERLOADED:
                return1 = 'Decimal'
                return3 = 'Money | Decimal'
                actiontype_start = ''
                actiontype_end = ''
            else:
                return1 = 'Money'
                return3 = 'Money'
                actiontype_start = f'self.currency.mint({linebreaker}'
                actiontype_end = ')'
            # Overloaded is never augmented (you can't augment-assignment
            # on a non-money; it always has to result in a money!)
            methods.append(OverloadedMethodTemplate(
                name=method_info.name,
                passthrough_name=method_info.passthrough_name,
                bookend_arg_separator=_ArgSeparator(
                    is_bookend=True,
                    do_linebreak=method_info.requires_long_signature),
                normal_arg_separator=_ArgSeparator(
                    is_bookend=False,
                    do_linebreak=method_info.requires_long_signature),
                context_kwarg=context_kwarg,
                context_passthrough=context_passthrough,
                linebreaker=linebreaker,
                actiontype_start=actiontype_start,
                actiontype_end=actiontype_end,
                return1=return1,
                return3=return3))

        else:
            linebreaker = _LineBreaker(
                do_linebreak=method_info.requires_long_signature,
                indent_level=4)
            if method_info.other_type is _Type.MONEY:
                template_cls = BinaryMethodReqMoneyTemplate
                other_ref = 'other.amount'
            elif method_info.other_type is _Type.SCALAR:
                template_cls = BinaryMethodReqScalarTemplate
                other_ref = 'other'
            else:
                raise RuntimeError(
                    'impossible branch: unknown binary other!',
                    method_info.other_type)

            if method_info.aug_for is not None:
                action_statement = (
                    f'self.amount = self.amount.{method_info.aug_for}'
                    + f'({linebreaker}{other_ref}{context_passthrough})'
                    + '\n            return self')
            elif method_info.return_type is _Type.MONEY:
                action_statement = (
                    f'return self.currency.mint({linebreaker}self.amount.'
                    + f'{method_info.name}({other_ref}{context_passthrough}))')
            else:
                action_statement = (
                    f'return self.amount.{method_info.name}'
                    + f'({linebreaker}{other_ref}{context_passthrough})')

            methods.append(template_cls(
                name=method_info.name,
                action_statement=action_statement,
                # We already handled the overloads!
                return_type=cast(str, method_info.return_type.value),
                context_kwarg=context_kwarg,
                bookend_arg_separator=_ArgSeparator(
                    is_bookend=True,
                    do_linebreak=method_info.requires_long_signature),
                normal_arg_separator=_ArgSeparator(
                    is_bookend=False,
                    do_linebreak=method_info.requires_long_signature),))

    module_text = templatey_env.render_sync(MoneymathModuleTemplate(
        methods=methods))
    dest_path.write_text(module_text, encoding='utf-8')


@dataclass(slots=True)
class _LineBreaker:
    do_linebreak: bool
    indent_level: int

    def __format__(self, fmtinfo=None) -> str:
        if self.do_linebreak:
            return f'\n{"    " * self.indent_level}'
        else:
            return ''


@dataclass(slots=True)
class _ArgSeparator:
    is_bookend: bool
    do_linebreak: bool

    def __format__(self, fmtinfo=None) -> str:
        if self.do_linebreak:
            return '\n            '
        elif self.is_bookend:
            return ''
        else:
            return ' '


@dataclass(slots=True)
class _ContextKwarg:
    has_context: bool
    do_linebreak: bool

    def __format__(self, fmtinfo=None) -> str:
        if self.has_context:
            if self.do_linebreak:
                return ',\n            context: Context | None = None'
            else:
                return ', context: Context | None = None'
        else:
            return ''


@dataclass(slots=True)
class _ContextPassthrough:
    has_context: bool
    is_unary: bool

    def __format__(self, fmtinfo=None) -> str:
        if self.has_context:
            if self.is_unary:
                return 'context=context'
            else:
                return ', context=context'
        else:
            return ''


@dataclass(slots=True)
class _MethodInfo:
    # TODO: add support for docstring!
    name: str
    has_context: bool
    other_type: _Type | None
    return_type: _Type
    aug_for: str | None = None
    override_long_signature: bool = False

    def __post_init__(self):
        if (
            self.return_type is _Type.OVERLOADED
            and self.other_type is not _Type.OVERLOADED
        ):
            raise ValueError('Return type overloaded but not other!')

        if self.aug_for is not None:
            if (self.name[0:2] + self.name[3:]) != self.aug_for:
                raise ValueError('Mismatching name/aug_for!')

            if self.return_type is not _Type.SELF:
                raise ValueError('Mismatching aug_for/type!')

    @property
    def requires_long_signature(self) -> bool:
        return (
            self.override_long_signature
            or (self.is_overloaded and self.has_context)
            or (not self.is_unary and self.has_context)
        )

    @property
    def passthrough_name(self) -> str:
        if self.aug_for is None:
            return self.name
        else:
            return self.aug_for

    @property
    def requires_scalar(self) -> bool:
        return self.other_type is _Type.SCALAR

    @property
    def requires_money(self) -> bool:
        return self.other_type is _Type.MONEY

    @property
    def is_unary(self) -> bool:
        return self.other_type is None

    @property
    def is_augmented(self) -> bool:
        return self.aug_for is not None

    @property
    def is_overloaded(self) -> bool:
        return self.other_type is _Type.OVERLOADED


class _Type(Enum):
    SCALAR = '_Scalar'
    MONEY = 'Money'
    BOOL = 'bool'
    NONE = 'None'
    INT = 'int'
    FLOAT = 'float'
    SELF = 'Self'
    OVERLOADED = None


# Things that don't make sense and are omitted:
# __pow__, __rpow__, __ipow__ -- how can you have money^x or x^money?
# __radd__, __rsub__ -- left-handed version will always be enough
# __complex__ -- Imaginary money? What is this, monopoly?
# Note that the order here also determines the order they're created in the
# codegen'd class!
MATH_METHODS_TO_CODEGEN = [
    _MethodInfo(
        name='__mul__',
        has_context=False,
        other_type=_Type.SCALAR,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__rmul__',
        has_context=False,
        other_type=_Type.SCALAR,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__add__',
        has_context=False,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__sub__',
        has_context=False,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__imul__',
        has_context=False,
        other_type=_Type.SCALAR,
        return_type=_Type.SELF,
        aug_for='__mul__'),
    _MethodInfo(
        name='__iadd__',
        has_context=False,
        other_type=_Type.MONEY,
        return_type=_Type.SELF,
        aug_for='__add__'),
    _MethodInfo(
        name='__isub__',
        has_context=False,
        other_type=_Type.MONEY,
        return_type=_Type.SELF,
        aug_for='__sub__'),
    _MethodInfo(
        name='__truediv__',
        has_context=False,
        other_type=_Type.OVERLOADED,
        return_type=_Type.OVERLOADED),
    _MethodInfo(
        name='__floordiv__',
        has_context=False,
        other_type=_Type.OVERLOADED,
        return_type=_Type.OVERLOADED),
    _MethodInfo(
        name='__mod__',
        has_context=False,
        other_type=_Type.OVERLOADED,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__itruediv__',
        has_context=False,
        other_type=_Type.SCALAR,
        return_type=_Type.SELF,
        aug_for='__truediv__'),
    _MethodInfo(
        name='__ifloordiv__',
        has_context=False,
        other_type=_Type.SCALAR,
        return_type=_Type.SELF,
        aug_for='__floordiv__'),
    _MethodInfo(
        name='__imod__',
        has_context=False,
        other_type=_Type.SCALAR,
        return_type=_Type.SELF,
        aug_for='__mod__'),
    _MethodInfo(
        name='__round__',
        has_context=False,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__trunc__',
        has_context=False,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__floor__',
        has_context=False,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__ceil__',
        has_context=False,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__int__',
        has_context=False,
        other_type=None,
        return_type=_Type.INT),
    _MethodInfo(
        name='__float__',
        has_context=False,
        other_type=None,
        return_type=_Type.FLOAT),
    _MethodInfo(
        name='__neg__',
        has_context=False,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__pos__',
        has_context=False,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='__abs__',
        has_context=False,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='compare',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.SCALAR),
    _MethodInfo(
        name='compare_signal',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.SCALAR),
    _MethodInfo(
        name='compare_total',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.SCALAR),
    _MethodInfo(
        name='compare_total_mag',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.SCALAR),
    _MethodInfo(
        name='remainder_near',
        has_context=True,
        other_type=_Type.OVERLOADED,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='shift',
        has_context=True,
        other_type=_Type.SCALAR,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='scaleb',
        has_context=True,
        other_type=_Type.SCALAR,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='rotate',
        has_context=True,
        other_type=_Type.SCALAR,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='same_quantum',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='next_minus',
        has_context=True,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='next_plus',
        has_context=True,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='normalize',
        has_context=True,
        other_type=None,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='is_finite',
        has_context=False,
        other_type=None,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='is_infinite',
        has_context=False,
        other_type=None,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='is_nan',
        has_context=False,
        other_type=None,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='is_qnan',
        has_context=False,
        other_type=None,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='is_signed',
        has_context=False,
        other_type=None,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='is_snan',
        has_context=False,
        other_type=None,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='is_zero',
        has_context=False,
        other_type=None,
        return_type=_Type.BOOL),
    _MethodInfo(
        name='next_toward',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='max',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='max_mag',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='min',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='min_mag',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
    _MethodInfo(
        name='copy_sign',
        has_context=True,
        other_type=_Type.MONEY,
        return_type=_Type.MONEY),
]


if __name__ == '__main__':
    codegen_moneymath_module()
