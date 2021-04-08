from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flasgger import Swagger
from flasgger.utils import swag_from
from flasgger import LazyString, LazyJSONEncoder


app = Flask(__name__)

# Constructer of api
api = Api(app)


app.config["SWAGGER"] = {"title": "Swagger-UI", "uiversion": 2}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,  # all in
            "model_filter": lambda tag: True,  # all in
        }
    ],
    "static_url_path": "/flasgger_static",
    # "static_folder": "static",  # must be set by user
    "swagger_ui": True,
    "specs_route": "/",
}

template = dict(
    swaggerUiPrefix=LazyString(lambda: request.environ.get("HTTP_X_SCRIPT_NAME", ""))
)

app.json_encoder = LazyJSONEncoder
swagger = Swagger(app, config=swagger_config, template=template)




def hello_banking_api():
    return jsonify({"message": "You can start creating account and transfer between acounts"})


dict_of_errors = {700: 'Account number must be greater than zero',
                  701: 'Account number must be unique',
                  702: 'Currency code should be one of them : TRY, USD, EUR',
                  703: 'balance cant be negative',
                  704: 'balance cant have precision greater then two',
                  705: 'Account dont exist',
                  800: 'Send amount must be bigger than zero',
                  801: 'Send amount precision cant be more then two',
                  802: 'Account(s) dont exist',
                  803: 'Sender and receiver accounts dont have the same currency code',
                  804: 'Sender dont have enough balance to make this transiction.',
                  805: 'Transaction dont exist'}


def precision(number):

    length_before_decimal = len(str(int(number))) + 1
    length_of = len(str(number))
    length_after_decimal = length_of - length_before_decimal
    return length_after_decimal


def check_posted_data(posted_data, method):
    if method == "create_account":
        duplicate_accountid = False
        for item in AccountModel.list_of_accounts:
            if posted_data["account number"] == item.account_id:
                duplicate_accountid = True
        if posted_data["account number"] <= 0:
            return 700
        elif duplicate_accountid:
            return 701
        elif not posted_data["currency code"] in ["TRY", "USD", "EUR"]:
            return 702
        elif posted_data["balance"] < 0:
            return 703
        elif precision(posted_data["balance"]) > 2:
            return 704
        else:
            return 200

    elif method == "transactions":
        counter = 0
        for i in range(len(AccountModel.list_of_accounts)):
            if posted_data["sender"] == AccountModel.list_of_accounts[i].account_id:
                sender_index = i
                counter = counter + 1
            elif posted_data["receiver"] == AccountModel.list_of_accounts[i].account_id:
                receiver_index = i
                counter = counter + 1
            elif counter == 2:
                break

        if posted_data["amount"] <= 0:
            return [800]
        elif precision(posted_data["amount"]) > 2:
            return [801]
        elif counter <= 1:
            return [802]
        elif AccountModel.list_of_accounts[receiver_index].currency_code !=\
                AccountModel.list_of_accounts[sender_index].currency_code:
            return [803]
        elif AccountModel.list_of_accounts[sender_index].balance < float(posted_data["amount"]):
            return [804]
        else:
            return [200, sender_index, receiver_index]


class AccountIterater(type):
    def __iter__(cls):
        return iter(cls.list_of_accounts)


class AccountModel(metaclass=AccountIterater):
    list_of_accounts = []

    def __init__(self, account_id, currency_code, balance):
        self.list_of_accounts.append(self)
        self.account_id = account_id
        self.currency_code = currency_code
        self.balance = float(balance)

    def setbalance(self, newbalance):
        self.balance = float(newbalance)

    def getbalance(self):
        return self.balance

    @staticmethod
    def update_amount(index, amount):

        AccountModel.list_of_accounts[index].balance = AccountModel.list_of_accounts[index].balance + amount


class CreateAccount(Resource):

    @swag_from("swagger/swagger_config.yml")
    def post(self):

        # Get posted data from the user and parse it as a json file.

        postedData = request.get_json()

        status_code = check_posted_data(postedData, "create_account")

        if status_code != 200:
            return_map_with_error = {'Message': dict_of_errors[status_code],
                                     'Status Code': status_code
                                     }
            return jsonify(return_map_with_error)

        acc_id = postedData["account number"]
        cur_code = postedData["currency code"]
        bal = postedData["balance"]

# Formatting variables
        bal = format(bal, '.2f')
        acc_id = int(acc_id)

# Creating object of AccountModel
        account_object = AccountModel(account_id=acc_id, currency_code=cur_code, balance=bal)

        returnmap = {

            'Message': "Account has been created with id {0} . Account  balance is  {2}{1}".format(acc_id, cur_code, bal),
            'Status Code': 200

        }

        return jsonify(returnmap)

    @swag_from("swagger/swagger_2config.yml")
    def get(self):

        accounts = []

        for item in AccountModel.list_of_accounts:
            accounts.append({'account id': item.account_id,
                             'currency code': item.currency_code,
                             'balance':  item.balance})

        if len(accounts) == 0:
            return jsonify({
            'Mesasge': "No accounts found.",
            'Status Code': 200
            })


        return jsonify({'Status Code': 200,
                        'Accounts': accounts
                       })

@swag_from("swagger/swagger_3config.yml")
@app.route("/accounts/<int:accountid>")
def get_account(accountid):

    accounts = []

    for item in AccountModel.list_of_accounts:

        if item.account_id == accountid:
            accounts.append({'sender': item.account_id,
                             'receiver': item.currency_code,
                             'amount': item.balance
                             })

    if len(accounts) == 0:
        return jsonify({
            'Status Code': 705,
            'Mesasge': dict_of_errors[705],
        })

    return jsonify({'Accounts': accounts,
                    'Status Code': 200
                   })


class TransactionIterater(type):
    def __iter__(cls):
        return iter(cls.list_of_transactions)


class TransactionModel(metaclass=TransactionIterater):
    list_of_transactions = []

    def __init__(self, sender_account, receiver_account, amount):
        self.list_of_transactions.append(self)
        self.sender_account = sender_account
        self.receiver_account = receiver_account
        self.amount = amount


class Transactions(Resource):

    @swag_from("swagger/swagger_tconfig.yml")
    def post(self):

        posteddata = request.get_json()

        sender_id = posteddata["sender"]
        receiver_id = posteddata["receiver"]
        amount_of_money = posteddata["amount"]

        sender_id = int(sender_id)
        receiver_id = int(receiver_id)
        amount_of_money = float(amount_of_money)


# Check_posted_data method return list with datas of status code , receiver and sender indexes of transaction accounts
        status = check_posted_data(posteddata, "transactions")

        if status[0] != 200:
            return_map_with_error = {'Message': dict_of_errors[status[0]],
                                     'Status Code': status[0]
                                     }
            return jsonify(return_map_with_error)

        AccountModel.update_amount(index=status[1], amount=(-amount_of_money))
        AccountModel.update_amount(index=status[2], amount=amount_of_money)

        transaction_object = TransactionModel(sender_account=sender_id,
                                              receiver_account=receiver_id, amount=amount_of_money)

        cur_code = AccountModel.list_of_accounts[status[1]].currency_code

        returnmap = {

            'message': " {0}{3} has been sent to {1} from {2} succesfully".format(amount_of_money, receiver_id,
                                                                                  sender_id, cur_code),
            'Status Code': 200
        }

        return jsonify(returnmap)

    @swag_from("swagger_t2config.yml")
    def get(self):

        transactions = []

        for i in range(len(TransactionModel.list_of_transactions)):
            transactions.append({'sender': TransactionModel.list_of_transactions[i].sender_account,
                                 'receiver': TransactionModel.list_of_transactions[i].receiver_account,
                                 'amount':  TransactionModel.list_of_transactions[i].amount})

        if len(transactions) == 0:
            return jsonify({
            'Mesasge': "No transactions found.",
            'Status Code': 200
            })


        return jsonify({'Transactions': transactions,
                        'Status Code': 200
                        })


@swag_from("swagger/swagger_t3config.yml")
@app.route("/transactions/<int:sender>")
def get_transaction(sender):

    transactions = []

    for item in TransactionModel.list_of_transactions:

        if item.sender_account == sender:
            transactions.append({'sender': item.sender_account,
                                  'receiver': item.receiver_account,
                                  'amount':  item.amount
                                  })

    retmap2 = {
        'Account Number': transactions,
        'Status Code': 200
    }

    if len(transactions) == 0:
        retmap2 = { "status code": "805",
                    "message": dict_of_errors[805]}

    return jsonify(retmap2)


api.add_resource(CreateAccount, "/accounts")
api.add_resource(Transactions, "/transactions")


if __name__ == '__main__':
    app.run(debug=False)
