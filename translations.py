# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 CEINPRO
"""Textos de interfaz y errores en castellano y euskera."""
import re
from flask import request

EU = {'Versión': 'Bertsioa', 'Control de Internet': 'Interneterako sarbidearen kontrola',
 'AULAS': 'IKASGELAK',
 'Aulas': 'Ikasgelak',
 'Actualizar': 'Eguneratu',
 'Cerrar sesión': 'Amaitu saioa',
 'Acceso': 'Sarbidea',
 'Introduce la contraseña del panel.': 'Sartu panelaren pasahitza.',
 'Contraseña': 'Pasahitza',
 'Entrar': 'Sartu',
 'Idioma': 'Hizkuntza',
 'Consultando': 'Kontsultatzen',
 'Sin configurar': 'Konfiguratu gabe',
 'Internet permitido': 'Internet baimenduta',
 'Internet bloqueado': 'Internet blokeatuta',
 'Pendiente de aplicar': 'Aplikatu gabe',
 'Revisar regla': 'Berrikusi araua',
 'Bloquear': 'Blokeatu',
 'Permitir': 'Baimendu',
 'Sin confirmar': 'Berretsi gabe',
 'Sesión caducada.': 'Saioa iraungi da.',
 'Respuesta inesperada del panel.': 'Panelaren ustekabeko erantzuna.',
 'No se pudo completar la operación.': 'Ezin izan da eragiketa burutu.',
 'Hay cambios pendientes en pfSense. Revísalos y aplícalos desde su interfaz.': 'Aplikatu gabeko '
                                                                                'aldaketak daude '
                                                                                'pfSense-n. Berrikusi '
                                                                                'eta aplikatu haren '
                                                                                'interfazetik.',
 'Aplicando el cambio en pfSense…': 'Aldaketa pfSense-n aplikatzen…',
 'El estado refleja la regla IPv4 aplicada en pfSense. Las conexiones abiertas pueden seguir activas hasta que caduquen o se eliminen sus estados.': 'Egoerak '
                                                                                                                                                     'pfSense-n '
                                                                                                                                                     'aplikatutako '
                                                                                                                                                     'IPv4 '
                                                                                                                                                     'araua '
                                                                                                                                                     'adierazten '
                                                                                                                                                     'du. '
                                                                                                                                                     'Irekitako '
                                                                                                                                                     'konexioek '
                                                                                                                                                     'aktibo '
                                                                                                                                                     'jarrai '
                                                                                                                                                     'dezakete '
                                                                                                                                                     'iraungi '
                                                                                                                                                     'arte '
                                                                                                                                                     'edo '
                                                                                                                                                     'haien '
                                                                                                                                                     'egoerak '
                                                                                                                                                     'ezabatu '
                                                                                                                                                     'arte.',
 'pfSense responde HTTP {status}. Revisa permisos y conexión.': 'pfSense-k HTTP {status} erantzun du. '
                                                                'Berrikusi baimenak eta konexioa.',
 'pfSense no ha confirmado la operación.': 'pfSense-k ez du eragiketa berretsi.',
 'No se puede validar el certificado HTTPS de pfSense.': 'Ezin da pfSense-ren HTTPS ziurtagiria '
                                                         'baliozkotu.',
 'No se ha podido confirmar la respuesta de pfSense. Actualiza antes de repetir el cambio.': 'Ezin izan '
                                                                                             'da '
                                                                                             'pfSense-ren '
                                                                                             'erantzuna '
                                                                                             'berretsi. '
                                                                                             'Eguneratu '
                                                                                             'aldaketa '
                                                                                             'berriro '
                                                                                             'egin '
                                                                                             'aurretik.',
 'No se encuentra una única regla para esta aula.': 'Ez da ikasgela honentzako arau bakar bat aurkitu.',
 'La regla del aula ha cambiado. Revisa origen, destino, interfaz y tipo en pfSense.': 'Ikasgelaren '
                                                                                       'araua aldatu '
                                                                                       'da. Berrikusi '
                                                                                       'jatorria, '
                                                                                       'helmuga, '
                                                                                       'interfazea eta '
                                                                                       'mota pfSense-n.',
 'La sesión ha caducado. Vuelve a entrar.': 'Saioa iraungi da. Sartu berriro.',
 'Sesión inválida. Recarga la página.': 'Saioa ez da baliozkoa. Kargatu berriro orria.',
 'Espera cinco minutos antes de volver a intentarlo.': 'Itxaron bost minutu berriro saiatu aurretik.',
 'La contraseña no es correcta.': 'Pasahitza ez da zuzena.',
 'Aula sin configurar.': 'Ikasgela konfiguratu gabe.',
 'Solicitud inválida.': 'Eskaera ez da baliozkoa.',
 'Hay cambios pendientes en pfSense. Revísalos y aplícalos en su interfaz antes de continuar.': 'Aplikatu '
                                                                                                'gabeko '
                                                                                                'aldaketak '
                                                                                                'daude '
                                                                                                'pfSense-n. '
                                                                                                'Berrikusi '
                                                                                                'eta '
                                                                                                'aplikatu '
                                                                                                'haren '
                                                                                                'interfazean '
                                                                                                'jarraitu '
                                                                                                'aurretik.',
 'El estado ha cambiado desde otra sesión. Actualiza antes de continuar.': 'Egoera beste saio batetik '
                                                                           'aldatu da. Eguneratu '
                                                                           'jarraitu aurretik.',
 'Las reglas se han reordenado. Actualiza y vuelve a intentarlo.': 'Arauen ordena aldatu da. Eguneratu '
                                                                   'eta saiatu berriro.',
 'pfSense mantiene cambios pendientes de aplicar.': 'pfSense-n aplikatu gabeko aldaketak daude '
                                                    'oraindik.',
 'El estado final de la regla no coincide con el solicitado.': 'Arauaren azken egoera ez dator bat '
                                                               'eskatutakoarekin.',
 ' La configuración puede haberse guardado. Comprueba la regla y Apply Changes en pfSense antes de repetir.': ' '
                                                                                                              'Baliteke '
                                                                                                              'konfigurazioa '
                                                                                                              'gorde '
                                                                                                              'izana. '
                                                                                                              'Egiaztatu '
                                                                                                              'araua '
                                                                                                              'eta '
                                                                                                              'Apply '
                                                                                                              'Changes '
                                                                                                              'aukera '
                                                                                                              'pfSense-n '
                                                                                                              'berriro '
                                                                                                              'saiatu '
                                                                                                              'aurretik.',
 '{action} Internet en {classroom}': '{classroom}: {action} Internet'}


def language():
    selected = request.cookies.get('language')
    if selected in ('es', 'eu'):
        return selected
    return request.accept_languages.best_match(['es', 'eu']) or 'es'


def translate(text):
    return EU.get(text, text) if language() == 'eu' else text


def classroom_name(classroom):
    if language() == 'eu' and classroom.get('name_eu'):
        return classroom['name_eu']
    name = classroom['name']
    match = re.fullmatch(r'Aula (\d+)', name)
    if match and language() == 'eu':
        return match.group(1) + '. ikasgela'
    return name
