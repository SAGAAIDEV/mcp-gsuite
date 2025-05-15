import json
from ..config.env import gsuite_config
from pydantic import BaseModel


class AccountInfo(BaseModel):

    email: str
    account_type: str
    extra_info: str

    def __init__(self, email: str, account_type: str, extra_info: str = ""):
        super().__init__(email=email, account_type=account_type, extra_info=extra_info)

    def to_description(self):
        return f"""Account for email: {self.email} of type: {self.account_type}. Extra info for: {self.extra_info}"""


class GmailAccountManager:
    def get_account_info(self) -> list[AccountInfo]:
        accounts_file = gsuite_config.accounts_file
        with open(accounts_file) as f:
            data = json.load(f)
            accounts = data.get("accounts", [])
            return [AccountInfo.model_validate(acc) for acc in accounts]

    def get_user_id_arg_schema(self) -> dict:
        account_descriptions = [a.to_description() for a in self.get_account_info()]
        return {
            "type": "string",
            "description": f"The EMAIL of the Google account for which you are executing this action. Can be one of: {', '.join(account_descriptions)}",
        }


def format_docstring_with_user_id_arg(func):
    """
    Decorator to format a function's docstring with the user_id_arg schema.
    """
    try:
        user_id_arg = GmailAccountManager().get_user_id_arg_schema()
        if func.__doc__:
            func.__doc__ = func.__doc__.format(user_id_arg=user_id_arg)
    except Exception:
        pass
    return func
