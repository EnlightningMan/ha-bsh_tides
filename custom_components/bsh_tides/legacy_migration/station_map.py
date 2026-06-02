"""Static legacy ``bshnr`` -> station slug mapping for config-entry migration.

Until 2026-05 the integration addressed stations by the BSH "bshnr" (e.g.
``111P``), stored in each config entry under the key ``bshnr``. The new
gdi.bsh.de OGC API addresses stations by slug (e.g. ``norderney_riffgat``)
and does **not** expose the old bshnr anywhere, so it cannot be derived at
runtime.

This table maps every bshnr that the retired ``wasserstand-nordsee.bsh.de``
API ever served to its slug. The slug is identical to the old ``seo_id``,
which means a migrated entry keeps the same entity ``unique_id``s
(``bsh_{seo_id}_{key}``) and the user's history/automations survive.

Source: archived ``wasserstand-nordsee.bsh.de/data/map.json`` (snapshot
2025-10-05). Used as an offline, rename-proof fallback by
``async_migrate_entry`` in this ``legacy_migration`` package.

TEMPORARY: part of the v1 -> v2 migration; see ``legacy_migration/__init__.py``
for the removal conditions.
"""

from __future__ import annotations

LEGACY_BSHNR_TO_SLUG: dict[str, str] = {
    '101P': 'borkum_fischerbalje',
    '103P': 'bremerhaven_alter_leuchtturm',
    '111P': 'norderney_riffgat',
    '502P': 'bremen_oslebshausen',
    '504B': 'brunsbuettel_ost',
    '505P': 'buesum_schleuse',
    '506P': 'cuxhaven_steubenhoeft',
    '507P': 'emden_grosse_seeschleuse',
    '508P': 'hamburg_st-pauli',
    '509A': 'helgoland_binnenhafen',
    '510P': 'husum_schleuse',
    '512P': 'wilhelmshaven_alter_vorhafen',
    '617P': 'list_hafen',
    '618P': 'munkmarsch',
    '620P': 'westerland',
    '622P': 'amrum_odde',
    '624P': 'hoernum_hafen',
    '628A': 'osterley',
    '629B': 'foehrer_ley_nord',
    '631P': 'wittduen_hafen',
    '632P': 'wyk',
    '635P': 'dagebuell',
    '636F': 'hooge_anleger',
    '637A': 'der_strand_hamburger_hallig',
    '637P': 'groede_anleger',
    '638P': 'schluettsiel',
    '642E': 'pellworm_hoogerfaehre',
    '645P': 'suederoogsand',
    '647A': 'pellworm_anleger',
    '649P': 'strucklahnungshoern',
    '664P': 'eider-sperrwerk_aussenpegel',
    '667B': 'meldorf_sperrwerk_aussenpegel',
    '677C': 'scharhoernriff_bake_a',
    '677P': 'scharhoern_bake_c',
    '678W': 'neuwerk_anleger',
    '681P': 'otterndorf',
    '683P': 'belum',
    '688P': 'brokdorf',
    '690P': 'stoer-sperrwerk_aussenpegel',
    '695P': 'glueckstadt',
    '698P': 'kollmar_kamperreihe',
    '700R': 'krueckau-sperrwerk_binnenpegel',
    '703P': 'grauerort',
    '704R': 'pinnau-sperrwerk_binnenpegel',
    '709P': 'stadersand',
    '711P': 'hetlingen',
    '714P': 'schulau',
    '715P': 'hamburg_blankenese',
    '717P': 'hamburg_cranz',
    '720P': 'hamburg_seemannshoeft',
    '724P': 'hamburg_harburg',
    '727P': 'hamburg_dove-elbe_einfahrt',
    '731P': 'hamburg_zollenspieker',
    '732D': 'geesthacht_wehr_unterpegel',
    '734P': 'alte_weser_leuchtturm',
    '735A': 'spieka_neufeld',
    '737P': 'dwarsgat',
    '741A': 'nordenham',
    '741B': 'rechtenfleth',
    '743P': 'brake',
    '744A': 'elsfleth_ohrt',
    '744P': 'elsfleth',
    '748P': 'oldenburg_drielake',
    '749P': 'bremen_farge',
    '750P': 'bremen_vegesack',
    '751P': 'bremen_wilhelm-kaisen-bruecke',
    '754P': 'wangerooge_nord',
    '756P': 'wangerooge_ost',
    '761P': 'schillig',
    '764B': 'hooksielplate',
    '768P': 'jade-weser-port',
    '770P': 'wilhelmshaven_neuer_vorhafen_seeschleuse',
    '777P': 'wangerooge_hafen',
    '778P': 'harlesiel',
    '779P': 'spiekeroog',
    '781P': 'langeoog_hafeneinfahrt',
    '782P': 'bensersiel',
    '796C': 'leyhoern_leybucht',
    '802P': 'knock',
    '806P': 'leerort',
    '808A': 'leda-sperrwerk_unterpegel',
    '814P': 'papenburg',
}
