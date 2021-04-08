from Tests.base_test import BaseTest
from app import AccountModel
import json


class TestHome(BaseTest):


    def test_Accounts(self):

        with self.app as c:

            acc_id = 1
            cur_code = "USD"
            bal = 4

            resp = c.post('/accounts' , json = {"account number": acc_id ,"currency code": cur_code, "balance" : bal} )
            self.assertEqual(resp.status_code,200)
            self.assertEqual(json.loads(resp.get_data()),
                             {"Message":"Account has been created with id {0} . Account  balance is  {2:.2f}{1}".format(acc_id,cur_code,bal),'Status Code': 200} )

#duplicate account error test

            resp = c.post('/accounts', json={"account number": acc_id, "currency code": cur_code, "balance": bal})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),{"Message":'Account number must be unique', 'Status Code': 701})

#Unvalid cur code error test

            unvalid_cur_code = "JPY"
            acc_id = 2

            resp = c.post('/accounts', json={"account number": acc_id, "currency code": unvalid_cur_code, "balance": bal})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),{"Message":'Currency code should be one of them : TRY, USD, EUR', 'Status Code': 702})

#negative balance error test

            negative_bal = -1000
            acc_id = 3
            
            resp = c.post('/accounts', json={"account number": acc_id, "currency code": cur_code, "balance": negative_bal})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),{'Message': 'balance cant be negative', 'Status Code': 703})
            
#precision error test

            acc_id = 4
            bal = 300.256

            resp = c.post('/accounts', json={"account number": acc_id, "currency code": cur_code, "balance": bal})
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),{'Message': 'balance cant have precision greater then two', 'Status Code': 704})

#get accounts

            resp = c.get('/accounts')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),{'Accounts': [{'account id': 1, 'balance': 4.0, 'currency code': 'USD'}],
 'Status Code': 200})

    def test_list_of_accounts(self):

        with self.app as c:
            resp = c.get("/accounts/1")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),{'Accounts': [{'amount': 4.0, 'receiver': 'USD', 'sender': 1}],
                                                          'Status Code': 200})
            resp = c.get("/accounts/968")
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()), {'Mesasge': 'Account dont exist', 'Status Code': 705})

    def test_Transactions(self):

        with self.app as c:
            acc2 = AccountModel(2,"USD",1000)
            acc3 = AccountModel(3,"USD",500)
            acc4 = AccountModel(4, "TRY", 1000)

            resp = c.post('/transactions',json = {"sender":2  ,"receiver":3 , "amount" :100 })
            self.assertEqual(resp.status_code,200)
            self.assertEqual((acc2.balance,acc3.balance),(900.0,600.0))

# Negative send amount

            resp = c.post('/transactions',json = {"sender":2  ,"receiver":3 , "amount" :-5 })
            self.assertEqual(resp.status_code,200)
            self.assertEqual(json.loads(resp.get_data()),{'Message': 'Send amount must be bigger than zero', 'Status Code': 800})

# Precision error

            resp = c.post('/transactions',json = {"sender":2  ,"receiver":3 , "amount" :5.555 })
            self.assertEqual(resp.status_code,200)
            self.assertEqual(json.loads(resp.get_data()),{'Message': 'Send amount precision cant be more then two', 'Status Code': 801})

# Account id error

            resp = c.post('/transactions',json = {"sender":356  ,"receiver":789 , "amount" :25 })
            self.assertEqual(resp.status_code,200)
            self.assertEqual(json.loads(resp.get_data()),{'Message': 'Account(s) dont exist', 'Status Code': 802})

# Currency match error

            resp = c.post('/transactions',json = {"sender":3  ,"receiver":4 , "amount" :25 })
            self.assertEqual(resp.status_code,200)
            self.assertEqual(json.loads(resp.get_data()),{'Message': 'Sender and receiver accounts dont have the same currency code',
 'Status Code': 803})


# Insufficient balance error

            resp = c.post('/transactions',json = {"sender":3  ,"receiver":2 , "amount" :25000 })
            self.assertEqual(resp.status_code,200)
            self.assertEqual(json.loads(resp.get_data()),{'Message': 'Sender dont have enough balance to make this transiction.',
 'Status Code': 804})

    def test_list_of_transactions(self):

        with self.app as c:
            acc2 = AccountModel(2, "USD", 1000)
            acc3 = AccountModel(3, "USD", 500)
            acc4 = AccountModel(4, "TRY", 1000)

            resp = c.get('/transactions/2')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),{'Account Number': [{'amount': 100.0, 'receiver': 3, 'sender': 2}],
 'Status Code': 200})

            resp = c.get('/transactions/7')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(json.loads(resp.get_data()),
                         {'message': 'Transaction dont exist', 'status code': '805'})






