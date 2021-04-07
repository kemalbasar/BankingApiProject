from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from apispec import APISpec
from marshmallow import Schema, fields
from apispec.ext.marshmallow import MarshmallowPlugin
from flask_apispec.extension import FlaskApiSpec
from flask_apispec.views import MethodResource
from flask_apispec import marshal_with, doc, use_kwargs

app = Flask(__name__)

# Constructer of api
api = Api(app)

app.config.update({
    'APISPEC_SPEC': APISpec(
        title='Bankin Api Doc',
        version='v1',
        plugins=[MarshmallowPlugin()],
        openapi_version='2.0.0'
    ),
    'APISPEC_SWAGGER_URL': '/swagger/',  # URI to access API Doc JSON
    'APISPEC_SWAGGER_UI_URL': '/swagger-ui/'  # URI to access UI of API Doc
})

docs = FlaskApiSpec(app)


class BankingAPIRequestSchema(Schema):
    class Meta:
        fields = ('Account Id', 'Currency Code', 'Balance')


class BankingAPITransactionRequestSchema(Schema):
    class Meta:
        fields = ('Sender', 'Receiver', 'Amount')


@app.route('/')
def hello_banking_api():
    return jsonify({"message": "You can start creating account and transfer between acounts"})


dict_of_errors = {700: 'Account number must be greater than zero',
                  701: 'Account number must be unique',
                  702: 'Currency code should be one of them : TRY, USD, EUR',
                  703: 'balance cant be negative',
                  704: 'balance cant have precision greater then two',
                  800: 'Send amount must be bigger than zero',
                  801: 'Send amount precision cant be more then two',
                  802: 'Account(s) dont exist',
                  803: 'Sender and receiver accounts dont have the same currency code',
                  804: 'Sender dont have enough balance to make this transiction.'}


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


class CreateAccount(Resource, MethodResource):

    @doc(description='Create Accounts', tags=['Account Methods'])
    @use_kwargs({"Account Id": fields.Integer(), "Currency Code": fields.String(), "Balance": fields.Float()}, location='json')
    @marshal_with(BankingAPIRequestSchema, code="200, 700, 701, 702, 703, 704", description="(Account number must be greater than zero),Account number must be unique, (Currency code should be one of them : TRY, USD, EUR), (Balance cant be negative),(Balance cant have precision greater then two)")
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

    @doc(description='List Accounts', tags=['Account Methods'])
    @marshal_with(BankingAPIRequestSchema, code="200")  # marshalling
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


        return jsonify({'Transactions': accounts,
                        'Status Code': 200
                        })


@doc(description='Get Account by ID', tags=['Account Methods'])
@marshal_with(BankingAPIRequestSchema, code=802, description="Account(s) dont exist")
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
            'Mesasge': "No transactions found.",
            'Status Code': 200
        })

    return jsonify({'Transactions': accounts,
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


class Transactions(Resource, MethodResource):

    @doc(description='Make Transactions', tags=['Transaction Methods'])
    @use_kwargs({"Sender": fields.Integer(), "Receiver": fields.Integer(), "Amount": fields.Float()}, location=('json'))
    @marshal_with(BankingAPITransactionRequestSchema, code="200, 700, 701, 702, 703, 704", description="(Send amount must be bigger than zero),(Send amount precision cant be more then two),('Account(s) dont exist'),('Sender and receiver accounts dont have the same currency code'),('Sender dont have enough balance to make this transiction.)")
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

    @doc(description='List All Transactions', tags=['Transaction Methods'])
    @marshal_with(BankingAPITransactionRequestSchema, code=200, description="Accounts")  # marshalling
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


@doc(description='List Transactions by Sender', tags=['Transaction Methods'])
@marshal_with(BankingAPITransactionRequestSchema, code=802, description="Account(s) dont exist")
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
        retmap2 = {"message": "transaction dont exist"}

    return jsonify(retmap2)


api.add_resource(CreateAccount, "/accounts")
api.add_resource(Transactions, "/transactions")
docs.register(CreateAccount,)
docs.register(Transactions)
docs.register(get_transaction)
docs.register(get_account)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
