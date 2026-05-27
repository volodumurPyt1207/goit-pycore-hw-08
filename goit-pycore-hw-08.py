"""
Команди:
    hello                              — привітання
    add <ім'я> <телефон>               — додати контакт / телефон
    change <ім'я> <старий> <новий>     — змінити телефон
    phone <ім'я>                       — показати телефони
    all                                — всі контакти
    add-birthday <ім'я> <DD.MM.YYYY>   — додати день народження
    show-birthday <ім'я>               — показати день народження
    birthdays                          — іменинники наступного тижня
    close / exit                       — зберегти і завершити роботу
"""

import pickle

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook() 

from collections import UserDict
from datetime import datetime, timedelta

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty.")
        super().__init__(value.strip())


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError(f"Phone '{value}' must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        target = self.find_phone(phone)
        if target is None:
            raise ValueError(f"Phone '{phone}' not found.")
        self.phones.remove(target)

    def edit_phone(self, old, new):
        target = self.find_phone(old)
        if target is None:
            raise ValueError(f"Phone '{old}' not found.")
        self.phones[self.phones.index(target)] = Phone(new)

    def find_phone(self, phone):
        return next((p for p in self.phones if p.value == phone), None)

    def add_birthday(self, date_str):
        self.birthday = Birthday(date_str)

    def __str__(self):
        phones   = "; ".join(p.value for p in self.phones) or "—"
        birthday = str(self.birthday) if self.birthday else "—"
        return (f"Name: {self.name.value:<20} "
                f"Phones: {phones:<30} "
                f"Birthday: {birthday}")


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name not in self.data:
            raise KeyError(f"'{name}'")
        del self.data[name]

    def get_upcoming_birthdays(self):
        today    = datetime.today().date()
        upcoming = []
        for record in self.data.values():
            if record.birthday is None:
                continue
            bd = record.birthday.value
            bd_this_year = bd.replace(year=today.year)
            if bd_this_year < today:
                bd_this_year = bd_this_year.replace(year=today.year + 1)
            delta = (bd_this_year - today).days
            if 0 <= delta <= 6:
                congrats = bd_this_year
                if congrats.weekday() == 5:
                    congrats += timedelta(days=2)
                elif congrats.weekday() == 6:
                    congrats += timedelta(days=1)
                upcoming.append({
                    "name":                record.name.value,
                    "congratulation_date": congrats.strftime("%d.%m.%Y"),
                })
        return upcoming

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e) if str(e) else "Give me name and phone please."
        except KeyError as e:
            return f"Contact {e} not found."
        except IndexError:
            return "Enter the argument for the command."
    return inner

def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd, *args = parts
    return cmd.lower(), args

@input_error
def add_contact(args, book):
    if len(args) < 2:
        raise IndexError
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book):
    if len(args) < 3:
        raise IndexError
    name, old_phone, new_phone = args[0], args[1], args[2]
    record = book.find(name)
    if record is None:
        raise KeyError(f"'{name}'")
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book):
    if not args:
        raise IndexError
    record = book.find(args[0])
    if record is None:
        raise KeyError(f"'{args[0]}'")
    phones = "; ".join(p.value for p in record.phones)
    return phones or "No phones recorded."


@input_error
def show_all(book):
    if not book.data:
        return "Address book is empty."
    return "\n".join(str(r) for r in sorted(book.data.values(),
                                            key=lambda r: r.name.value))


@input_error
def add_birthday(args, book):
    if len(args) < 2:
        raise IndexError
    name, date_str = args[0], args[1]
    record = book.find(name)
    if record is None:
        raise KeyError(f"'{name}'")
    record.add_birthday(date_str)
    return "Birthday added."


@input_error
def show_birthday(args, book):
    if not args:
        raise IndexError
    record = book.find(args[0])
    if record is None:
        raise KeyError(f"'{args[0]}'")
    if record.birthday is None:
        return f"No birthday recorded for {args[0]}."
    return str(record.birthday)


@input_error
def birthdays(book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    return "\n".join(f"{e['name']}: {e['congratulation_date']}" for e in upcoming)

def main():
    book = load_data()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if not command:
            continue

        if command in ("close", "exit"):
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(book))

        else:
            print("Invalid command.")

    save_data(book)  


if __name__ == "__main__":
    main()