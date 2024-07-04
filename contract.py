"""
CSC148, Winter 2024
Assignment 1

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

All of the files in this directory and all subdirectories are:
Copyright (c) 2022 Bogdan Simion, Diane Horton, Jacqueline Smith
"""
import datetime
from math import ceil
from typing import Optional, Union
from bill import Bill
from call import Call


# Constants for the month-to-month contract monthly fee and term deposit
MTM_MONTHLY_FEE = 50.00
TERM_MONTHLY_FEE = 20.00
TERM_DEPOSIT = 300.00

# Constants for the included minutes and SMSs in the term contracts (per month)
TERM_MINS = 100

# Cost per minute and per SMS in the month-to-month contract
MTM_MINS_COST = 0.05

# Cost per minute and per SMS in the term contract
TERM_MINS_COST = 0.1

# Cost per minute and per SMS in the prepaid contract
PREPAID_MINS_COST = 0.025


class Contract:
    """ A contract for a phone line

    This class is not to be changed or instantiated. It is an Abstract Class.

    === Public Attributes ===
    start:
         starting date for the contract
    bill:
         bill for this contract for the last month of call records loaded from
         the input dataset
    """
    start: Union[datetime.date, None]
    bill: Optional[Bill]

    def __init__(self, start: datetime.date) -> None:
        """ Create a new Contract with the <start> date, starts as inactive
        """
        self.start = start
        self.bill = None

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>. 
        This may be the first month of the contract. 
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        DO NOT CHANGE THIS METHOD
        """
        raise NotImplementedError

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancelation is requested.
        """
        self.start = None
        return self.bill.get_cost()


class TermContract(Contract):
    """ A term contract for a phone line

    === Public Attributes ===
    end:
         ending date for the contract
    free_minutes:
         number of free minutes included each month
    """
    end: datetime.date
    free_minutes: int

    def __init__(self, start: datetime.date, end: datetime.date) -> None:
        """ Create a new TermContract with the <start> date and <end> date.
        """
        super().__init__(start)
        self.end = end
        self.free_minutes = TERM_MINS

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>.
        This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        If the contract is past its end date, carry over the term deposit.
        """
        # Check if it's the first month of the contract
        if month == self.start.month and year == self.start.year:
            bill.add_fixed_cost(TERM_DEPOSIT)

        # Fixed costs/rates
        bill.add_fixed_cost(TERM_MONTHLY_FEE)
        bill.set_rates("TERM", TERM_MINS_COST)

    def bill_call(self, call: Call) -> None:
        """ Add the <call> to the bill.

        Precondition:
        - a bill has already been created for the month+year when the <call>
        was made. In other words, you can safely assume that self.bill has been
        already advanced to the right month+year.
        """
        # Check if the customer has free minutes
        if self.bill.free_min < self.free_minutes:
            # Use up free minutes
            minutes_used = min(self.free_minutes, ceil(call.duration / 60.0))
            self.bill.add_free_minutes(minutes_used)

            # Check if there are additional minutes to bill
            excess_minutes = ceil((call.duration - minutes_used * 60) / 60.0)
            if excess_minutes > 0:
                self.bill.add_billed_minutes(excess_minutes)
        else:
            # No free minutes left, bill the call
            self.bill.add_billed_minutes(ceil(call.duration / 60.0))

    def cancel_contract(self) -> float:
        """ Return the amount owed in order to close the phone line associated
        with this term contract.

        Precondition:
        - a bill has already been created for the month+year when this contract
        is being cancelled. In other words, you can safely assume that self.bill
        exists for the right month+year when the cancellation is requested.
        """
        self.start = None
        if self.end is not None and self.end < datetime.date.today():
            # The contract is past its end date, refund the term deposit
            return -TERM_DEPOSIT + TERM_MONTHLY_FEE
        else:
            # The contract is cancelled before the end date, forfeit the deposit
            return 0.0


class MTMContract(Contract):
    """ A month-to-month contract for a phone line.

    === Additional Attribute ===
    end:
         end date for the contract (None for month-to-month contracts)
    """

    def __init__(self, start: datetime.date) -> None:
        """ Create a new month-to-month contract with the <start> date.
        """
        super().__init__(start)

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>.
        This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.
        """
        # Fixed costs/rates
        bill.add_fixed_cost(MTM_MONTHLY_FEE)
        bill.set_rates("MTM", MTM_MINS_COST)


TOP_UP_THRESHOLD = -10.00
TOP_UP_AMOUNT = -25.00


class PrepaidContract(Contract):
    """ A prepaid contract for a phone line.
    """
    balance: float

    def __init__(self, start: datetime.date, balance: float) -> None:
        """ Create a new PrepaidContract with the <start> date and
        initial_balance.
        """
        super().__init__(start)
        self.balance = balance

    def new_month(self, month: int, year: int, bill: Bill) -> None:
        """ A new month has begun corresponding to <month> and <year>.
        This may be the first month of the contract.
        Store the <bill> argument in this contract and set the appropriate rate
        per minute and fixed cost.

        Carry over the balance from the previous month.
        If the balance is less than $10, top-up with $25 in credit.
        """

        # Carry over the balance from the previous month
        bill.add_fixed_cost(-self.balance)

        # Check if the balance is less than $10 and top-up with $25
        if self.balance < TOP_UP_THRESHOLD:
            self.balance -= TOP_UP_AMOUNT
        bill.set_rates("prepaid", PREPAID_MINS_COST)

    def cancel_contract(self) -> float:
        """ Return the amount owed or to be refunded when cancelling
        the prepaid contract.
        """
        if self.balance <= 0:
            # If the balance is negative, forfeit the amount
            self.start = None
            return 0.0
        else:
            # If the balance is positive, return the amount
            amount_to_return = self.balance
            self.start = None
            return amount_to_return


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-import-modules': [
            'python_ta', 'typing', 'datetime', 'bill', 'call', 'math'
        ],
        'disable': ['R0902', 'R0913'],
        'generated-members': 'pygame.*'
    })
