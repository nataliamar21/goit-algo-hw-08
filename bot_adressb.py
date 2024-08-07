import re
import pickle
from datetime import datetime, date, timedelta
from collections import UserDict


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name cannot be empty.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not self.validate(value):
            raise ValueError("Invalid phone number. Must be exactly 10 digits.")
        super().__init__(value)

    @staticmethod
    def validate(value):
        return bool(re.fullmatch(r'\d{10}', value))


class Birthday(Field):
    def __init__(self, value):
        try:
            # Перетворення рядка на об'єкт datetime.date
            datetime.strptime(value, "%d.%m.%Y")
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        phone_to_remove = next((p for p in self.phones if p.value == phone_number), None)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)
        else:
            raise ValueError("Phone number not found.")

    def edit_phone(self, old_phone_number, new_phone_number):
        if not Phone.validate(new_phone_number):
            raise ValueError("Invalid new phone number. Must be exactly 10 digits.")
        self.remove_phone(old_phone_number)
        self.add_phone(new_phone_number)

    def find_phone(self, phone_number):
        return next((p for p in self.phones if p.value == phone_number), None)

    def add_birthday(self, birthday_date):
        self.birthday = Birthday(birthday_date)

    def days_to_birthday(self):
        if self.birthday:
            today = date.today()
            birth_date = datetime.strptime(self.birthday.value, "%d.%m.%Y").date()
            next_birthday = birth_date.replace(year=today.year)

            if next_birthday < today:
                next_birthday = next_birthday.replace(year=today.year + 1)

            return (next_birthday - today).days

        return None

    def __str__(self):
        birthday_info = f", birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday_info}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise ValueError("Record not found.")

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birth_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
                birthday_this_year = birth_date.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                days_until_birthday = (birthday_this_year - today).days

                if 0 <= days_until_birthday <= days:
                    congrats_date = birthday_this_year
                    # Переносимо день народження, якщо він припадає на вихідний
                    if congrats_date.weekday() in (5, 6):  # субота, неділя
                        congrats_date += timedelta(days=(7 - congrats_date.weekday()))

                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": congrats_date.strftime("%d.%m.%Y")
                    })
        return upcoming_birthdays

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "This contact does not exist."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Invalid input. Please provide the correct arguments."
    return inner


@input_error
def add_contact(args, book: AddressBook):
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
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Phone number updated."
    return "Contact not found."


@input_error
def show_phone(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return f"Phones for {name}: " + ", ".join(p.value for p in record.phones)
    return "Contact not found."


@input_error
def show_all(book: AddressBook):
    if book:
        return "\n".join(str(record) for record in book.values())
    else:
        return "No contacts found."


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday_date = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday_date)
        return f"Birthday added for {name}."
    return "Contact not found."


@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name}'s birthday is on {record.birthday.value}."
    elif record:
        return f"{name} does not have a birthday set."
    return "Contact not found."


@input_error
def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays found."

    messages = []
    for birthday in upcoming_birthdays:
        messages.append(f"{birthday['name']} - Congratulate on {birthday['congratulation_date']}")

    return "\n".join(messages)


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args


def save_data(book, filename="addressbook.pkl"):
    """Зберігає дані адресної книги у файл."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    """Завантажує дані адресної книги з файлу."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


def main():
    book = load_data()  # Завантажуємо існуючі дані при старті програми

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ").strip()
        if not user_input:
            continue

        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)  # Зберігаємо дані при виході з програми
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
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()