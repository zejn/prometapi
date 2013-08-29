===================================
API za prometne podatke v Sloveniji
===================================


Namen
=====

Namen te storitve je ponuditi v nadalnjo rabo podatke o prometnem stanju v
Sloveniji. Storitev je s strani Kiberpipe brezplačna, potrebno pa je
spoštovati avtorsko pravico in navesti vire podatkov, ki jih uporabljate.

Format zapisa
=============

Vsi podatki so na voljo v JSON zapisu. Vsak odgovor ima poleg izvirnih
podatkov, še nekaj dodatnih podatkov:

copyright
  string, vsebuje naziv nosilca avtorske pravice nad podatki.

updated
  float, unix timestamp, vsebuje podatek o tem, kdaj so bili podatki
  posodobljeni.

Kjer so izvirni podatki koordinate, so dodane še koordinate v prostorskem
referenčnem sistemu WGS84.

Vsak klic v primeru napake vrne odgovor::

  null

Podatki
=======

Podatki so trenutno na voljo na www.opendata.si. Hostname se lahko v
prihodnje spremeni.

Dogodki na cestah
-----------------

URL: `/promet/events/`_

Vir podatkov: Direkcija RS za ceste, http://promet.si


Burja
-----

URL: `/promet/burja/`_

Vir podatkov: Direkcija RS za ceste, http://promet.si

Burja - znaki
-------------

URL: `/promet/burjaznaki/`_

Vir podatkov: Direkcija RS za ceste, http://promet.si

Števci prometa
--------------

URL: `/promet/counters/`_

Vir podatkov: Direkcija RS za ceste, http://promet.si

Parkirišča LPT
--------------

URL: `/promet/parkirisca/lpt/`_

Vir podatkov: Javno podjetje Ljubljanska parkirišča in tržnice, d.o.o., http://www.lpt.si

Bicikelj
--------

URL: `/promet/bicikelj/list/`_

Vir podatkov: `Bicikelj.si`_

.. _`/promet/events/`: http://opendata.si/promet/events/
.. _`/promet/burja/`: http://opendata.si/promet/burja/
.. _`/promet/burjaznaki/`: http://opendata.si/promet/burjaznaki/
.. _`/promet/counters/`: http://opendata.si/promet/counters/
.. _`/promet/parkirisca/lpt/`: http://opendata.si/promet/parkirisca/lpt/
.. _`/promet/bicikelj/list/`: http://opendata.si/promet/bicikelj/list/
.. _`Bicikelj.si`: http://www.bicikelj.si/
