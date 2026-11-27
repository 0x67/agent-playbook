#!/bin/sh
set -e
cat > shipping.py <<'X'
class Address:
    def __init__(self):
        self._street = None
        self._city = None

    def get_street(self):
        return self._street

    def set_street(self, street):
        self._street = street

    def get_city(self):
        return self._city

    def set_city(self, city):
        self._city = city


class AddressBuilder:
    def __init__(self):
        self._street = None
        self._city = None

    def street(self, street):
        self._street = street
        return self

    def city(self, city):
        self._city = city
        return self

    def build(self):
        address = Address()
        address.set_street(self._street)
        address.set_city(self._city)
        return address


class Shipment:
    def __init__(self, order_id, street, city, weight_kg, express, insured, gift_wrap):
        self.order_id = order_id
        self.address = AddressBuilder().street(street).city(city).build()
        self.weight_kg = weight_kg
        self.express = express
        self.insured = insured
        self.gift_wrap = gift_wrap
        self.is_packed = False
        self.is_shipped = False
        self.is_delivered = False
        self.is_returned = False


class FlatRate:
    def price(self, shipment):
        return 5 + shipment.weight_kg * 2


class ShippingRateFactory:
    def create(self):
        return FlatRate()


class ShipmentStore(dict):
    def add(self, shipment):
        self[shipment.order_id] = shipment

    def ship(self, order_id):
        shipment = self[order_id]
        shipment.is_shipped = True
        shipment.is_packed = True
X
