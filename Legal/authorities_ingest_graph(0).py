key <AE12> { [  equal, plus			] };

    key <AD01> { [  U1C67			] };
    key <AD02> { [  U1C63			] };
    key <AD03> { [  U1C6E			] };
    key <AD04> { [  U1C68			] };
    key <AD05> { [  U1C74, U1C5B		] };
    key <AD06> { [  U1C6D  			] };
    key <AD07> { [  U1C69			] };
    key <AD08> { [  U1C64			] };
    key <AD09> { [  U1C5A, U1C73		] };
    key <AD10> { [  U1C6F  			] };
    key <AD11> { [  bracketleft, braceleft	] };
    key <AD12> { [  bracketright, braceright 	] };
    key <BKSL> { [  U1C7F, U1C7E		] };

    key <AC01> { [  U1C5F  			] };
    key <AC02> { [  U1C65			] };
    key <AC03> { [  U1C70, U1C6B		] };
    key <AC04> { [  U1C5D  			] };
    key <AC05> { [  U1C5C			] };
    key <AC06> { [  U1C66, U1C77		] };
    key <AC07> { [  U1C61  			] };
    key <AC08> { [  U1C60			] };
    key <AC09> { [  U1C5E			] };
    key <AC10> { [  semicolon, U1C7A		] };
    key <AC11> { [  apostrophe, quotedbl	] };

    key <AB01> { [  U1C72			] };
    key <AB02> { [  U1C7D			] };
    key <AB03> { [  U1C6A			] };
    key <AB04> { [  U1C76			] };
    key <AB05> { [  U1C75			] };
    key <AB06> { [  U1C71, U1C78		] };
    key <AB07> { [  U1C62, U1C6C		] };
    key <AB08> { [  comma, less			] };
    key <AB09> { [  U1C79, greater		] };
    key <AB10> { [  slash, question		] };

    key <RALT> {
	symbols[Group1] = [ Mode_switch, Multi_key ],
	virtualMods = AltGr
    };

    include "level3(ralt_switch)"
};


partial alphanumeric_keys
xkb_symbols "ori" {
    // Inscript layout for Oriya  
    // Author: G Karunakar <karunakar@freedomink.org>
    // Date: Wed Nov 13 18:16:19 IST 2002

    name[Group1]= "Oriya";

    key <AE01> { [  U0b67			] };
    key <AE02> { [  U0b68			] };
    key <AE03> { [  U0b69			] };
    key <AE04> { [  U0b6a			] };
    key <AE05> { [  U0b6b			] };
    key <AE06> { [  U0b6c			] };
    key <AE07> { [  U0b6d			] };
    key <AE08> { [  U0b6e			] };
    key <AE09> { [  U0b6f			] };
    key <AE10> { [  U0b66			] };
    key <AE11> { [  U0b03			] };
    key <AE12> { [  U0b43, U0b0b	] };

    key <AD01> { [  U0b4c, U0b14	] };
    key <AD02> { [  U0b48, U0b10	] };
    key <AD03> { [  U0b3e, U0b06	] };
    key <AD04> { [  U0b40, U0b08	] };
    key <AD05> { [  U0b42, U0b0a	] };
    key <AD06> { [  U0b2c, U0b2d	] };
    key <AD07> { [  U0b39, U0b19	] };
    key <AD08> { [  U0b17, U0b18	] };
    key <AD09> { [  U0b26, U0b27	] };
    key <AD10> { [  U0b1c, U0b1d	] };
    key <AD11> { [  U0b21, U0b22	] };
    key <AD12> { [  U0b3c, U0b1e	] };

    key <AC01> { [  U0b4b, U0b13	] };
    key <AC02> { [  U0b47, U0b0f	] };
    key <AC03> { [  U0b4d, U0b05	] };
    key <AC04> { [  U0b3f, U0b07	] };
    key <AC05> { [  U0b41, U0b09	] };
    key <AC06> { [  U0b2a, U0b2b	] };
    key <AC07> { [  U0b30			] };
    key <AC08> { [  U0b15, U0b16	] };
    key <AC09> { [  U0b24, U0b25	] };
    key <AC10> { [  U0b1a, U0b1b	] };
    key <AC11> { [  U0b1f, U0b20	] };

    key <AB02> { [  U0b02, U0b01	] };
    key <AB03> { [  U0b2e, U0b23	] };
    key <AB04> { [  U0b28			] };
    key <AB05> { [  U0b35			] };
    key <AB06> { [  U0b32, U0b33	] };
    key <AB07> { [  U0b38, U0b36	] };
    key <AB08> { [  comma     , U0b37	] };
    key <AB09> { [  period    				] };
    key <AB10> { [  U0b2f, U0040	] };

    key <RALT> {
	symbols[Group1] = [ Mode_switch, Multi_key ],
	virtualMods = AltGr
    };
    include "rupeesign(4)"
    include "level3(ralt_switch)"
};

// based on a keyboard map from an 'xkb/symbols/tml' file
// INSCRIPT
partial alphanumeric_keys
xkb_symbols "tam" {
      name[Group1]= "Tamil (Inscript)";

      key <TLDE> { [      U0BCA, U0B92	]	};

      // Mainly numbers.
      key <AE01> { [      U0BE7 		]	};
      key <AE02> { [      U0BE8 		]	};
      key <AE03> { [      U0BE9 		]	};
      key <AE04> { [      U0BEA 		]	};
      key <AE05> { [      U0BEB 		]	};
      key <AE06> { [      U0BEC 		]	};
      key <AE07> { [      U0BED        	]	};
      key <AE08> { [      U0BEE 		]	};
      key <AE09> { [      U0BEF, parenleft	]	};
      key <AE10> { [      U0BF0, parenright	]	};
      key <AE11> { [      U0BF1, U0B83  ]	};
      key <AE12> { [      U0BF2, plus	] 	};

// Mainly long vowels

      key <AD01> { [      U0BCC,  U0B94 ]	};
      key <AD02> { [      U0BC8,  U0B90 ]	};
      key <AD03> { [      U0BBE,  U0B86 ]	};
      key <AD04> { [      U0BC0,  U0B88 ]	};
      key <AD05> { [      U0BC2,  U0B8A ]	};

// Mainly voiced consonants

      key <AD07> { [      U0BB9, U0B99	]	};
      key <AD10> { [      U0B9c 	]	};
      key <AD12> { [      U0B9E				]	};

// Mainly short vowels
      key <AC01> { [      U0BCB,  U0B93 ]	};
      key <AC02> { [      U0BC7,  U0B8F ]	};
      key <AC03> { [      U0BCD,  U0B85 ]	};
      key <AC04> { [      U0BBF,  U0B87 ]	};
      key <AC05> { [      U0BC1,  U0B89 ]	};

// Mainly unvoiced consonants

      key <AC06> { [      U0BAA 		]	};
      key <AC07> { [      U0BB0,  U0BB1 ]	};
      key <AC08> { [      U0B95 		]	};
      key <AC09> { [      U0BA4 		]	};
      key <AC10> { [      U0B9A 		]	};
      key <AC11> { [      U0B9F 		]	};
      key <BKSL> { [      U005C, U007C	]	};//backslash-bar  - Changed to Unicode

      key <AB01> { [      U0BC6,  U0B8E	]	};
      key <AB02> { [      U0B82   		]       };
      key <AB03> { [      U0BAE,  U0BA3 ]       };
      key <AB04> { [      U0BA8,  U0BA9 ]       };
      key <AB05> { [      U0BB5,  U0BB4 ]       };
      key <AB06> { [      U0BB2,  U0BB3 ]       };
      key <AB07> { [      U0BB8,  U0BB6	]       };
      key <AB08> { [      comma,      U0BB7 ]       };
      key <AB09> { [      period,     U0964 ]       };
      key <AB10> { [      U0BAF,  question  ]       };

      include "level3(ralt_switch)"
      include "rupeesign(4)"
};

partial alphanumeric_keys
xkb_symbols "tam_tamilnet" {

// Description: A keymap based on the TamilNet'99 typewriter keyboard 
// Encoding: Unicode (http://www.unicode.org)
// Author: Thuraiappah Vaseeharan <vasee@ieee.org>
// Modifed by: Malathi S <malathiramya@gmail.com>
// Secondary contact: Sri Ramadoss M <amachu@au-kbc.org>
// Date  : Fri Sep 4 11:32:00 CST 2009
// Mapping:

    name[Group1]= "Tamil (TamilNet '99)";

    // granthas
    key <TLDE> {  [ apostrophe, asciitilde ] };
    key <AE01> {  [ U0031, exclam ] } ;
    key <AE02> {  [ U0032, at ] } ;
    key <AE03> {  [ U0033, numbersign ] } ;
    key <AE04> {  [ U0034, U0BF9 ] } ;
    key <AE05> {  [ U0035, percent ] } ;
    key <AE06> {  [ U0036, asciicircum ] } ;
    key <AE07> {  [ U0037, ampersand ] } ;
    key <AE08> {  [ U0038, asterisk ] } ;
    key <AE09> {  [ U0039, parenleft ] } ;
    key <AE10> {  [ U0030, parenright ] } ;
    key <AE11> {  [ minus, underscore ] };
    key <AE12> {  [ equal, plus	] };


    // Qrow
    key <AD01> {  [ U0B9E, U0BB6 ] };
    key <AD02> {  [ U0BB1, U0BB7 ] };
    key <AD03> {  [ U0BA8, U0BB8 ] };
    key <AD04> {  [ U0B9A, U0BB9 ] };
    key <AD05> {  [ U0BB5, U0B9C ] };
    key <AD06> {  [ U0BB2 ] };
    key <AD07> {  [ U0BB0 ] };
    key <AD08> {  [ U0BC8, U0B90 ] };
    key <AD09> {  [ U0BCA, U0BCB ] };
    key <AD10> {  [ U0BBF, U0BC0 ] };
    key <AD11> {  [ U0BC1, U0BC2 ] };

    // Arow
    key <AC01> { [ U0BAF ] };
    key <AC02> { [ U0BB3 ] };
    key <AC03> { [ U0BA9 ] };
    key <AC04> { [ U0B95 ] };
    key <AC05> { [ U0BAA ] };
    key <AC06> { [ U0BBE, U0BB4 ] };
    key <AC07> { [ U0BA4 ] };
    key <AC08> { [ U0BAE ] };
    key <AC09> { [ U0B9F ] };
    key <AC10> { [ U0BCD, U0B83 ] };
    key <AC11> { [ U0B99 ] };

    // Zrow
    key <AB01> { [ U0BA3 ]  };
    key <AB02> { [ U0B92, U0B93 ]  };
    key <AB03> { [ U0B89, U0B8A ]  };
    key <AB04> { [ U0B8E, U0B8F ]  };
    key <AB05> { [ U0BC6, U0BC7 ]  };
    key <AB06> { [ U0B94, U0BCC ]  };
    key <AB07> { [ U0B85, U0B86 ]  };
    key <AB08> { [ U0B87, U0B88 ]  };
};

partial alphanumeric_keys
xkb_symbols "tam_tamilnet_with_tam_nums" {

// Description: A keymap based on the TamilNet'99 typewriter keyboard 
// Encoding: Unicode (http://www.unicode.org)
// Author: Malathi S <malathiramya@gmail.com>
// Secondary contact: Sri Ramadoss M <amachu@au-kbc.org>
// Date  : Fri Sep 4 11:33:00 CST 2009
// Mapping:

      name[Group1]= "Tamil (TamilNet '99 with Tamil numerals)";

      // Mainly numbers.
      key <TLDE> { [ apostrophe, asciitilde ] };
      key <AE01> { [ U0BE7, exclam ] };
      key <AE02> { [ U0BE8, at ] };
      key <AE03> { [ U0BE9, numbersign ] };
      key <AE04> { [ U0BEA, U0BF9 ] };
      key <AE05> { [ U0BEB, percent ] };
      key <AE06> { [ U0BEC, asciicircum ] };
      key <AE07> { [ U0BED, ampersand ] };
      key <AE08> { [ U0BEE, asterisk ] };
      key <AE09> { [ U0BEF, parenleft ] };
      key <AE10> { [ U0BE6, parenright ] };
      key <AE11> { [ minus, underscore ] };
      key <AE12> { [ equal, plus ] };


    // Qrow
    key <AD01> {  [ U0B9E, U0BB6 ] };
    key <AD02> {  [ U0BB1, U0BB7 ] };
    key <AD03> {  [ U0BA8, U0BB8 ] };
    key <AD04> {  [ U0B9a, U0BB9 ] };
    key <AD05> {  [ U0BB5, U0B9c ] };
    key <AD06> {  [ U0BB2 ] };
    key <AD07> {  [ U0BB0 ] };
    key <AD08> {  [ U0BC8, U0B90 ] };
    key <AD09> {  [ U0BCA, U0BCB ] };
    key <AD10> {  [ U0BBF, U0BC0 ] };
    key <AD11> {  [ U0BC1, U0BC2 ] };

    // Arow
    key <AC01> { [ U0BAF ] };
    key <AC02> { [ U0BB3 ] };
    key <AC03> { [ U0BA9 ] };
    key <AC04> { [ U0B95 ] };
    key <AC05> { [ U0BAA ] };
    key <AC06> { [ U0BBE, U0BB4 ] };
    key <AC07> { [ U0BA4 ] };
    key <AC08> { [ U0BAE ] };
    key <AC09> { [ U0B9F ] };
    key <AC10> { [ U0BCD, U0B83 ] };
    key <AC11> { [ U0B99 ] };

    // Zrow
    key <AB01> { [ U0BA3 ]  };
    key <AB02> { [ U0B92, U0B93 ]  };
    key <AB03> { [ U0B89, U0B8A ]  };
    key <AB04> { [ U0B8E, U0B8F ]  };
    key <AB05> { [ U0BC6, U0BC7 ]  };
    key <AB06> { [ U0B94, U0BCC ]  };
    key <AB07> { [ U0B85, U0B86 ]  };
    key <AB08> { [ U0B87, U0B88 ]  };
};

partial alphanumeric_keys
xkb_symbols "tam_tamilnet_TSCII" {

// Description	: A Tamil typewrite-style keymap 
//		  loosely based on TamilNet'99 reommendations 
// Encoding	: TSCII (http://www.tscii.org)
// Author	: Thuraiappah Vaseeharan <vasee@ieee.org>
// Last Modified: Sat Jan  5 17:11:26 CST 2002

    name[Group1]= "Tamil (TamilNet '99, TSCII encoding)";

    key <AE01> {  [ 0x10000b7, 0x10000a4 ] }; // aytham
    key <AE02> {  [ 0x1000082, 0x10000a5 ] }; // shri
    key <AE03> {  [ 0x1000083, 0x1000088 ] }; // ja
    key <AE04> {  [ 0x1000084, 0x1000089 ] }; // sha
    key <AE05> {  [ 0x1000085, 0x100008a ] }; // sa
    key <AE06> {  [ 0x1000086, 0x100008b ] }; // ha
    key <AE07> {  [ 0x1000087, 0x100008c ] }; // ksha

    // Qrow
    key <AD01> {  [ 0x10000bb, 0x100009a ] }; // nja
    key <AD02> {  [ 0x10000c8, 0x10000da ] }; // Ra
    key <AD03> {  [ 0x10000bf, 0x10000d1 ] }; // NNa
    key <AD04> {  [ 0x10000ba, 0x10000cd ] }; // ca
    key <AD05> {  [ 0x10000c5, 0x10000d7 ] }; // va
    key <AD06> {  [ 0x10000c4, 0x10000d6 ] }; // la
    key <AD07> {  [ 0x10000c3, 0x10000d5 ] }; // ra
    key <AD08> {  [ 0x10000a8, 0x10000b3 ] }; // sangili, ai
    key <AD09> {  [ 0x10000ca, 0x10000cb ] }; // di, dI
    key <AD10> {  [ 0x10000a2, 0x10000a3 ] }; // visiri
    key <AD11> {  [ dead_acute, 0x10000a3 ] }; // Ukaaram

    // Arow
    key <AC01> { [ 0x10000c2, 0x10000d4 ] }; // ya
    key <AC02> { [ 0x10000c7, 0x10000d9 ] }; // La
    key <AC03> { [ 0x10000c9, 0x10000db ] }; // na
    key <AC04> { [ 0x10000b8, 0x10000cc ] }; // ka
    key <AC05> { [ 0x10000c0, 0x10000d2 ] }; // pa
    key <AC06> { [ dead_grave,0x10000a1 ] }; // pulli,aravu
    key <AC07> { [ 0x10000be, 0x10000d0 ] }; // tha
    key <AC08> { [ 0x10000c1, 0x10000d3 ] }; // ma
    key <AC09> { [ 0x10000bc, 0x10000ce ] }; // da
    key <AC10> { [ 0x10000c6, 0x10000d8 ] }; // zha
    key <AC11> { [ 0x10000b9, 0x1000099 ] }; // nga

    // Zrow
    key <AB01> { [ 0x10000bd, 0x10000cf ] }; // Na
    key <AB02> { [ 0x10000b4, 0x10000b5 ] }; // o, O
    key <AB03> { [ 0x10000af, 0x10000b0 ] }; // u, U
    key <AB04> { [ 0x10000b1, 0x10000b2 ] }; // e, E
    key <AB05> { [ 0x10000a6, 0x10000a7 ] }; // kombus
    key <AB06> { [ 0x10000b6, 0x10000aa ] }; // au
    key <AB07> { [ 0x10000ab, 0x10000ac ] }; // a, A
    key <AB08> { [ 0x10000fe, 0x10000ae ] }; // i, I
};

partial alphanumeric_keys
xkb_symbols "tam_tamilnet_TAB" {

// Description: A keymap based on the TamilNet'99 typewriter keyboard 
// Encoding: TAB (http://www.tamilnet99.org)
// Author: Thuraiappah Vaseeharan <t_vasee@yahoo.com>
// Date  : Sun Aug 12 02:23:00 CDT 2001

    name[Group1]= "Tamil (TamilNet '99, TAB encoding)";

    // numeral row
    key <AE01> {  [ 0x10000e7, 0x10000a7 ] } ;
    key <AE02> {  [ 0x10000fa, 0x10000a8 ] } ;
    key <AE03> {  [ 0x10000fb ] } ;
    key <AE04> {  [ 0x10000fc ] } ;
    key <AE05> {  [ 0x10000fd ] } ;
    key <AE06> {  [ 0x10000fe ] } ;
    key <AE07> {  [ 0x10000ff ] } ;

    // q-row
    key <AD01> {  [ 0x10000eb, 0x10000b3 ] };
    key <AD02> {  [ 0x10000f8, 0x10000c1 ] };
    key <AD03> {  [ 0x10000ef, 0x10000b8 ] };
    key <AD04> {  [ 0x10000ea, 0x10000b2 ] };
    key <AD05> {  [ 0x10000f5, 0x10000be ] };
    key <AD06> {  [ 0x10000f4, 0x10000bd ] };
    key <AD07> {  [ 0x10000f3, 0x10000bc ] };
    key <AD08> {  [ 0x10000ac, 0x10000e4 ] };
    key <AD09> {  [ 0x10000ae, 0x10000af ] };
    key <AD10> {  [ 0x10000a4, 0x10000a6 ] };
    key <AD11> {  [ dead_circumflex, 0x10000a6 ] }; // Ukaaram

    // a-row
    key <AC01> {  [ 0x10000f2, 0x10000bb ] };
    key <AC02> {  [ 0x10000f7, 0x10000c0 ] };
    key <AC03> {  [ 0x10000f9, 0x10000c2 ] };
    key <AC04> {  [ 0x10000e8, 0x10000b0 ] };
    key <AC05> {  [ 0x10000f0, 0x10000b9 ] };
    key <AC06> {  [ 0x10000a2, 0x10000a3 ] };
    key <AC07> {  [ 0x10000ee, 0x10000b6 ] };
    key <AC08> {  [ 0x10000f1, 0x10000ba ] };
    key <AC09> {  [ 0x10000ec, 0x10000b4 ] };
    key <AC10> {  [ 0x10000f6, 0x10000bf ] };
    key <AC11> {  [ 0x10000e9, 0x10000b1 ] };

    // z-row
    key <AB01> {  [ 0x10000ed, 0x10000b5 ] };
    key <AB02> {  [ 0x10000e5, 0x10000e6 ] };
    key <AB03> {  [ 0x10000e0, 0x10000e1 ] };
    key <AB04> {  [ 0x10000e2, 0x10000e3 ] };
    key <AB05> {  [ 0x10000aa, 0x10000ab ] };
    key <AB06> {  [ 0x10000ac, 0x10000a3 ] };
    key <AB07> {  [ 0x10000dc, 0x10000dd ] };
    key <AB08> {  [ 0x10000de, 0x10000df ] };
};

partial alphanumeric_keys
xkb_symbols "tel" {

    // Inscript layout for Telugu using Unicode 
    // Author: G Karunakar <karunakar@freedomink.org>
    // Date:
    // See layout at http://www.indlinux.org/keymap/telugu.php

    name[Group1]= "Telugu";

    key <TLDE> { [  U0c4a, U0c12	] };
    key <AE01> { [  U0c67			] };
    key <AE02> { [  U0c68			] };
    key <AE03> { [  U0c69, numbersign	] };
    key <AE04> { [  U0c6a, dollar		] };
    key <AE05> { [  U0c6b, percent		] };
    key <AE06> { [  U0c6c, asciicircum	] };
    key <AE07> { [  U0c6d, ampersand	] };
    key <AE08> { [  U0c6e, asterisk	] };
    key <AE09> { [  U0c6f, parenleft	] };
    key <AE10> { [  U0c66, parenright	] };
    key <AE11> { [  U0c03, underscore	] };
    key <AE12> { [  U0c43, U0c0b	] };
    key <BKSP> { [  BackSpace			] };

    key <AD01> { [  U0c4c, U0c14	] };
    key <AD02> { [  U0c48, U0c10	] };
    key <AD03> { [  U0c3e, U0c06	] };
    key <AD04> { [  U0c40, U0c08	] };
    key <AD05> { [  U0c42, U0c0a	] };
    key <AD06> { [  U0c2c, U0c2d	] };
    key <AD07> { [  U0c39, U0c19	] };
    key <AD08> { [  U0c17, U0c18	] };
    key <AD09> { [  U0c26, U0c27	] };
    key <AD10> { [  U0c1c, U0c1d	] };
    key <AD11> { [  U0c21, U0c22	] };
    key <AD12> { [  U0c1e			] };

    key <AC01> { [  U0c4b, U0c13	] };
    key <AC02> { [  U0c47, U0c0f	] };
    key <AC03> { [  U0c4d, U0c05	] };
    key <AC04> { [  U0c3f, U0c07	] };
    key <AC05> { [  U0c41, U0c09	] };
    key <AC06> { [  U0c2a, U0c2b	] };
    key <AC07> { [  U0c30, U0c31	] };
    key <AC08> { [  U0c15, U0c16	] };
    key <AC09> { [  U0c24, U0c25	] };
    key <AC10> { [  U0c1a, U0c1b	] };
    key <AC11> { [  U0c1f, U0c20	] };

    key <AB01> { [  U0c46, U0c0e	] };
    key <AB02> { [  U0c02, U0c01	] };
    key <AB03> { [  U0c2e, U0c23	] };
    key <AB04> { [  U0c28			] };
    key <AB05> { [  U0c35			] };
    key <AB06> { [  U0c32, U0c33	] };
    key <AB07> { [  U0c38, U0c36	] };
    key <AB08> { [  comma     , U0c37	] };
    key <AB09> { [  period    				] };
    key <AB10> { [  U0c2f, U0040	] };

    key <RALT> {        
        symbols[Group1] = [ Mode_switch, Multi_key ],
        virtualMods = AltGr
    };
    include "rupeesign(4)"
    include "level3(ralt_switch)"
};

//Name                  :       Sarala
//Description           :       This is an adaptation of the Sarala keyboard (http://www.medhajananam.org/sarala/) developed 
//                              by Krishna Dhullipalla. Because of the way keyboard shortcuts are laid out in KDE, the keyboard
//                              modifiers had to be changed. The layout does not take any part of the original Sarala keyboard 
//                              code however. It has been developed from scratch, so the experience may differ.
//			        
//                              There is a ibus-m17n version of Sarala layout developed by Satya Pothamsetti <potham@gmail.com> on 
//                              http://www.medhajananam.org/.
//Standard		:	Supports Unicode 9.0.	 
//Help			:	This layout differs slightly from the layout on Medhajenanam. The layout has been depicted in the 
//				pdf file attached to this post on Sarala google group.
//				(https://groups.google.com/forum/#!topic/sarala-keyboard/-gsa90dUFcs).
//
//Layout Developed by   :       Krishna Dhullipalla <krishnadvr@yahoo.com> (http://www.medhajananam.org/)
//Author                :       Venkat R Akkineni <venkatram.akkineni@india.com>
//Date			:	Apr 28 2017
partial alphanumeric_keys
xkb_symbols "tel-sarala"
{
    name[Group1] = "Telugu (Sarala)";
    key.type="FOUR_LEVEL";
    // sequence 									  base, shift, alt, alt + shift
    key <AB01> { [          U0C4A,          U0C12                                 ] }; // ొ ఒ
    key <AB02> { [          U0C42,          U0C0A                                 ] }; // ూ ఊ
    key <AB03> { [          U0C21,          U0C22                                 ] }; // డ ఢ
    key <AB04> { [          U0C35,          U0C39                                 ] }; // వ హ
    key <AB05> { [          U0C2C,          U0C2D                                 ] }; // బ భ
    key <AB06> { [          U0C28,          U0C23                                 ] }; // న ణ
    key <AB07> { [          U0C2E,          U0C01                                 ] }; // మ ఁ
    key <AB08> { [         U002C,          U0C1E,      leftcaret 	    	  ] }; // , ఞ <
    key <AB09> { [         U002E,          U0C19,     rightcaret              	  ] }; // . ఙ >
    key <AB10> { [          U0C36,       question,      KP_Divide                 ] }; // శ ? /
    key <AC01> { [          U0C2F,          U0C3D           			  ] }; // య ఽ
    key <AC02> { [          U0C02,          U0C03                                 ] }; // ం ః
    key <AC03> { [          U0C26,          U0C27                                 ] }; // ద ధ
    key <AC04> { [          U0C4D,          U0C05                                 ] }; // ్ అ
    key <AC05> { [          U0C17,          U0C18                                 ] }; // గ ఘ
    key <AC06> { [          U0C1A,          U0C1B,          U0C58,          U0C59 ] }; // చ ఛ ౘ ౙ
    key <AC07> { [          U0C3E,          U0C06                                 ] }; // ా ఆ
    key <AC08> { [          U0C15,          U0C16,          U0C62,          U0C63 ] }; // క ఖ ౢ ౣ
    key <AC09> { [          U0C32,          U0C33,          U0C0C,          U0C61 ] }; // ల ళ ఌ ౡ
    key <AC10> { [          U0C1F,          U0C20,      semicolon,          colon ] }; // ట ఠ ; :
    key <AC11> { [     quoteright,       quotedbl	    	    		  ] }; // ' " 
    key <AD01> { [          U0C46,          U0C0E,          U0C44,          U0C34 ] }; // ె ఎ ౄ ఴ
    key <AD02> { [          U0C38,          U0C37,          U0C44                 ] }; // స ష ౄ
    key <AD03> { [          U0C47,          U0C0F,          U0C44                 ] }; // ే ఏ ౄ
    key <AD04> { [          U0C30,          U0C31,          U0C44,          U0C60 ] }; // ర ఱ ౄ ౠ
    key <AD05> { [          U0C24,          U0C25                                 ] }; // త థ
    key <AD06> { [          U0C40,          U0C08                                 ] }; // ీ ఈ
    key <AD07> { [          U0C41,          U0C09                                 ] }; // ు ఉ
    key <AD08> { [          U0C3F,          U0C07                                 ] }; // ి ఇ
    key <AD09> { [          U0C4B,          U0C13                                 ] }; // ో ఓ
    key <AD10> { [          U0C2A,          U0C2B                                 ] }; // ప ఫ
    key <AD11> { [          U0C1C,          U0C1D,    bracketleft,      braceleft ] }; // జ ఝ [ {
    key <AD12> { [          U0C48,          U0C10,   bracketright,     braceright ] }; // ై ఐ ] }
    key <AE01> { [           KP_1,         exclam,          U0C67,          U0C78 ] }; // 1 ! ౦ ౸
    key <AE02> { [           KP_2,             at,          U0C68,          U0C79 ] }; // 2 @ ౨ ౹
    key <AE03> { [           KP_3,     numbersign,          U0C69,          U0C7A ] }; // 3 # ౩ ౺
    key <AE04> { [           KP_4,         dollar,          U0C6A,          U0C7B ] }; // 4 $ ౪ ౻
    key <AE05> { [           KP_5,        percent,          U0C6B,          U0C7C ] }; // 5 % ౫ ౼
    key <AE06> { [           KP_6,    asciicircum,          U0C6C,          U0C7D ] }; // 6 ^ ౬ ౽
    key <AE07> { [           KP_7,      ampersand,          U0C6D,          U0C7E ] }; // 7 & ౭ ౾
    key <AE08> { [           KP_8,    KP_Multiply,          U0C6E,          U0C7F ] }; // 8 * ౮ ౿
    key <AE09> { [           KP_9,         U0028,           U0C6F,          U20B9 ] }; // 9 ( ౯ ₹
    key <AE10> { [           KP_0,         U0029,           U0C66,          U0C55 ] }; // 0 ) ౦ ౕ
    key <AE11> { [    KP_Subtract,       underbar,       NoSymbol,          U0C56 ] }; // - _  ౖ
    key <AE12> { [       KP_Equal,         KP_Add                                 ] }; // = +
    key <BKSL> { [          U0C4C,          U0C14,          U0964,          U0965 ] }; // ౌ ఔ । ॥
    key <TLDE> { [          U0C43,          U0C0B,      quoteleft,     asciitilde ] }; // ృ ఋ ` ~
    
    include "level3(ralt_switch)" 
};

partial alphanumeric_keys 
xkb_symbols "urd-phonetic" {
    include "pk(urd-phonetic)"
    name[Group1]= "Urdu (phonetic)";
};

partial alphanumeric_keys
xkb_symbols "urd-phonetic3" {
    include "pk(urd-crulp)"
    name[Group1]= "Urdu (alt. phonetic)";
};

partial alphanumeric_keys
xkb_symbols "urd-winkeys" {
    include "pk(urd-nla)"
    name[Group1]= "Urdu (Windows)";
};

// based on a keyboard map from an 'xkb/symbols/gur' file

partial alphanumeric_keys
xkb_symbols "guru" {
      name[Group1]= "Punjabi (Gurmukhi)";

      // Mainly numbers.
      key <AE01> { [      U0A67 		]	};
      key <AE02> { [      U0A68		]	};
      key <AE03> { [      U0A69, U0A71	]	};
      key <AE04> { [      U0A6A, U0A74	 	]	};
      key <AE05> { [      U0A6B, U262C		]	};
      key <AE06> { [      U0A6C  	 	]	};
      key <AE07> { [      U0A6D 		]	};
      key <AE08> { [      U0A6e  	 	]	};
      key <AE09> { [      U0A6F, parenleft 	]	};
      key <AE10> { [      U0A66, parenright ]	};
      key <AE11> { [      U0A03 	 	]	};
      key <AE12> { [      equal,	plus 	]	};

// Mainly long vowels

      key <AD01> { [      U0A4C, U0A14  ]	};
      key <AD02> { [      U0A48, U0A10  ]	};
      key <AD03> { [      U0A3E, U0A06  ]	};
      key <AD04> { [      U0A40, U0A08  ]	};
      key <AD05> { [      U0A42, U0A0A  ]	};

// Mainly voiced consonants

      key <AD06> { [      U0A2C, U0A2D 	]	};
      key <AD07> { [      U0A39, U0A19 	]	};
      key <AD08> { [      U0A17, U0A18 	]	};
      key <AD09> { [      U0A26, U0A27 	]	};
      key <AD10> { [      U0A1C, U0A1D 	]	};
      key <AD11> { [      U0A21, U0A22 	]	};
      key <AD12> { [      U0A3C, U0A1E 	]	};

// Mainly short vowels
      key <AC01> { [      U0A4B, U0A13  ]	};
      key <AC02> { [      U0A47, U0A0F  ]	};
      key <AC03> { [      U0A4D, U0A05  ]	};
      key <AC04> { [      U0A3F, U0A07  ]	};
      key <AC05> { [      U0A41, U0A09  ]	};

// Mainly unvoiced consonants

      key <AC06> { [      U0A2A, U0A2B 	]	};
      key <AC07> { [      U0A30, U0A5C 	]	};
      key <AC08> { [      U0A15, U0A16 	]	};
      key <AC09> { [      U0A24, U0A25 	]	};
      key <AC10> { [      U0A1A, U0A1B 	]	};
      key <AC11> { [      U0A1F, U0A20 	]	};
      key <BKSL> { [      U005C, U007C	]	};

      key <AB01> { [      z, 	 U0A01	]       };
      key <AB02> { [      U0A02, U0A70, U0A71  ]       };
      key <AB03> { [      U0A2E, U0A23  ]       };
      key <AB04> { [      U0A28, U0A28  ]       };
      key <AB05> { [      U0A35, U0A35  ]       };
      key <AB06> { [      U0A32, U0A33  ]       };
      key <AB07> { [      U0A38, U0A36  ]       };
      key <AB08> { [      comma,     less       ]       };
      key <AB09> { [      period,    U0964  ]       };
      key <AB10> { [      U0A2F, question   ]       };

    include "rupeesign(4)"
    include "level3(ralt_switch)"
};

//Name		:	Jhelum (Refind Inscript)
//Description	:	A Jhelum keyboard layout for Gurmukhi (Punjabi)
//			http://www.satluj.org/Jhelum.html
//Modified for Inscript to make
//Original Author :	Amanpreet Singh Alam <apreet.alam@gmail.com

partial alphanumeric_keys
xkb_symbols "jhelum" {
      name[Group1] = "Punjabi (Gurmukhi Jhelum)";
          key.type="FOUR_LEVEL";

     // Roman digits
     key <TLDE>  { [  apostrophe, asciitilde, U0A02,U0A01 ] }; // apostrophe: anusvara, candrabindu
     key <AE01>  { [   1,exclam,	U0A67,	exclam	   ] };
     key <AE02>  { [   2,at,	U0A68,	at	   ] };
     key <AE03>  { [   3,numbersign, U0A69,	numbersign ] };
     key <AE04>  { [   4,dollar,	U0A6A		 ] };
     key <AE05>  { [   5,percent,U0A6B,	percent    ] };
     key <AE06>  { [   6,U0A73, U0A6C,asciicircum ] };
     key <AE07>  { [   7,U0A72,U0A6D,ampersand  ] };
     key <AE08>  { [   8,asterisk,U0A6E,	asterisk   ] };
     key <AE09>  { [   9,parenleft,U0A6F,parenleft  ] };
     key <AE10>  { [   0,parenright,U0A66,parenright ] };
     key <AE11>	{ [   minus,underscore] };
     key <AE12>	{ [   equal,plus] };
     key <BKSL>  { [   U0964,U0965,U007C,U005C] }; //pipe : danda, double danda

     //Q Row	
     key <AD01>   { [   U0A4C, 	U0A14   ] };  // Q: oo, ooh
     key <AD02>   { [   U0A48,  	U0A10	] };  // W: ee, ae
     key <AD03>   { [   U0A3E,   U0A06  ] };  // E: a, aa
     key <AD04>   { [   U0A40,	U0A08, U20B9  	] };  // R: ee, ai, rupeesign
     key <AD05>   { [   U0A42,   U0A0A   ] };  // T: u, uu
     key <AD06>   { [   U0A30,	U0A5C   ] };  // Y: ra, raa
     key <AD07>   { [   U0A26,   U0A27   ] };  // U: tha, thha
     key <AD08>   { [   U0A17,   U0A18, U0A5A   ] };  // I:ga, gha
     key <AD09>   { [   U0A24,   U0A1F   ] };  // O: ta, tha
     key <AD10>   { [   U0A2A,   U0A5E, VoidSymbol,U0A5E  ] };  // P: pa, pha
     key <AD11>   { [   U0A21,   U0A22,   bracketleft,   braceleft   ] };
     key <AD12>	 { [   U0A19,   U0A1E,   bracketright, braceright   ] };

     //A Row
     key <AC01>   { [   U0A4B,	 U0A13  ] };   // A: o, oo
     key <AC02>   { [   U0A47,    U0A0F   ] };  // S: e, ee
     key <AC03>   { [   U0A4D,    U0A05   ] };  // D: halant, aa
     key <AC04>   { [   U0A3F,    U0A07   ] };  // F: i, aa
     key <AC05>   { [   U0A41,    U0A09   ] };  // G: u, uh
     key <AC06>   { [   U0A39,    U0A20   ] };  // H: ha, thha
     key <AC07>   { [   U0A1C,    U0A1D, U0A5B   ] };  // J: ja, jha
     key <AC08>   { [   U0A15,    U0A16,VoidSymbol ,U0A59   ] };  // K: ka, kha
     key <AC09>   { [   U0A32,	 U0A25, U0A33   ] };  // L: la, tha
     key <AC10>   { [   U0A38,   colon, U0A36  ] }; //; sa
     key <AC11>   { [apostrophe, quotedbl ] };

     //Z Row
     key <AB01>   { [   U0A71,	 U0A3C 	 ] };  // Z: addak, par bindi
     key <AB02>   { [   U0A02,    U0A70	 ] };  // X: bindi, tippi
     key <AB03>   { [   U0A1A,    U0A1B   ] };  // C: ca, cha
     key <AB04>   { [   U0A35,    U0A2F   ] };  // V: va, ya
     key <AB05>   { [   U0A2C,    U0A2D   ] };  // B: ba, bha
     key <AB06>   { [   U0A28,    U0A23   ] };  // N: na, nha
     key <AB07>   { [   U0A2E, U0A2E       ] };  // M: ma
     key <AB08>   { [   comma,    U262C	 ] };// comma: comma, dev abbreviation sign
     key <AB09>   { [   period,   U0A74 	 ] };  // period: period, nukta
     key <AB10>   { [   slash,   question ] };

//    modifier_map Shift  { Shift_L };
//    modifier_map Lock   { Caps_Lock };
//    modifier_map Control{ Control_L };
//    modifier_map Mod3   { Mode_switch };
    include "level3(ralt_switch)"
};

partial alphanumeric_keys
xkb_symbols "olpc" {

// Contact: Walter Bender <walter@laptop.org>

  include "in(deva)"
  key <TLDE> { [	U094A,	U0912 ] }; // DEVANAGARI VOWEL SIGN SHORT O; DEVANAGARI LETTER SHORT O
  key <AE01> { [	U0967,	U090D ] }; // DEVANAGARI DIGIT ONE; DEVANAGARI LETTER CANDRA E
  key <AE02> { [	U0968,	U0945 ] }; // DEVANAGARI DIGIT TWO; DEVANAGARI VOWEL SIGN CANDRA E
  key <AE03> { [	U0969	 ] }; // DEVANAGARI DIGIT THREE;
  key <AE04> { [	U096A	 ] }; // DEVANAGARI DIGIT FOUR;
  key <AE05> { [	U096B	 ] }; // DEVANAGARI DIGIT FIVE;
  key <AE06> { [	U096C	 ] }; // DEVANAGARI DIGIT SIX;
  key <AE07> { [	U096D	 ] }; // DEVANAGARI DIGIT SEVEN;
  key <AE08> { [	U096E	 ] }; // DEVANAGARI DIGIT EIGHT;
  key <AE09> { [	U096F,	parenleft ] }; // DEVANAGARI DIGIT NINE;
  key <AE10> { [	U0966,	parenright ] }; // DEVANAGARI DIGIT ZERO;
  key <AE11> { [	minus,		U0903 ] }; // DEVANAGARI SIGN VISARGA;
  key <AE12> { [	U0943,	U090B ] }; // DEVANAGARI VOWEL SIGN VOCALIC R; DEVANAGARI LETTER VOCALIC R

  key <AD01> { [	U094C,	U0914 ] }; // DEVANAGARI VOWEL SIGN AU; DEVANAGARI LETTER AU
  key <AD02> { [	U0948,	U0910 ] }; // DEVANAGARI VOWEL SIGN AI; DEVANAGARI LETTER AI
  key <AD03> { [	U093E,	U0906 ] }; // DEVANAGARI VOWEL SIGN AA; DEVANAGARI LETTER AA
  key <AD04> { [	U0940,	U0908 ] }; // DEVANAGARI VOWEL SIGN II; DEVANAGARI LETTER II
  key <AD05> { [	U0942,	U090A ] }; // DEVANAGARI VOWEL SIGN UU; DEVANAGARI LETTER UU
  key <AD06> { [	U092C,	U092D ] }; // DEVANAGARI LETTER BA; DEVANAGARI LETTER BHA
  key <AD07> { [	U0939,	U0919 ] }; // DEVANAGARI LETTER HA; DEVANAGARI LETTER NGA
  key <AD08> { [	U0917,	U0918 ] }; // DEVANAGARI LETTER GA; DEVANAGARI LETTER GHA
  key <AD09> { [	U0926,	U0927 ] }; // DEVANAGARI LETTER DA; DEVANAGARI LETTER DHA
  key <AD10> { [	U091C,	U091D ] }; // DEVANAGARI LETTER JA; DEVANAGARI LETTER JHA
  key <AD11> { [	U0921,	U0922 ] }; // DEVANAGARI LETTER DDA; DEVANAGARI LETTER DDHA
  key <AD12> { [	U093C,	U091E ] }; // DEVANAGARI SIGN NUKTA; DEVANAGARI LETTER NYA

  key <BKSL> { [	U0949,	U0911 ] }; // DEVANAGARI VOWEL SIGN CANDRA O; DEVANAGARI LETTER CANDRA O

  key <AC01> { [	U094B,	U0913 ] }; // DEVANAGARI VOWEL SIGN O; DEVANAGARI LETTER O
  key <AC02> { [	U0947,	U090F ] }; // DEVANAGARI VOWEL SIGN E; DEVANAGARI LETTER E
  key <AC03> { [	U094D,	U0905 ] }; // DEVANAGARI SIGN VIRAMA; DEVANAGARI LETTER A
  key <AC04> { [	U093F,	U0907 ] }; // DEVANAGARI VOWEL SIGN I; DEVANAGARI LETTER I
  key <AC05> { [	U0941,	U0909 ] }; // DEVANAGARI VOWEL SIGN U; DEVANAGARI LETTER U
  key <AC06> { [	U092A,	U092B ] }; // DEVANAGARI LETTER PA; DEVANAGARI LETTER PHA
  key <AC07> { [	U0930,	U0931 ] }; // DEVANAGARI LETTER RA; DEVANAGARI LETTER RRA
  key <AC08> { [	U0915,	U0916 ] }; // DEVANAGARI LETTER KA; DEVANAGARI LETTER KHA
  key <AC09> { [	U0924,	U0925 ] }; // DEVANAGARI LETTER TA; DEVANAGARI LETTER THA
  key <AC10> { [	U091A,	U091B ] }; // DEVANAGARI LETTER CA; DEVANAGARI LETTER CHA
  key <AC11> { [	U091F,	U0920 ] }; // DEVANAGARI LETTER TTA; DEVANAGARI LETTER TTHA

  key <AB01> { [	U0946,	U090E ] }; // DEVANAGARI VOWEL SIGN SHORT E; DEVANAGARI LETTER SHORT E
  key <AB02> { [	U0902,	U0901 ] }; // DEVANAGARI SIGN ANUSVARA; DEVANAGARI SIGN CANDRABINDU
  key <AB03> { [	U092E,	U0923 ] }; // DEVANAGARI LETTER MA; DEVANAGARI LETTER NNA
  key <AB04> { [	U0928,	U0929 ] }; // DEVANAGARI LETTER NA; DEVANAGARI LETTER NNNA
  key <AB05> { [	U0935,	U0934 ] }; // DEVANAGARI LETTER VA; DEVANAGARI LETTER LLLA
  key <AB06> { [	U0932,	U0933 ] }; // DEVANAGARI LETTER LA; DEVANAGARI LETTER LLA
  key <AB07> { [	U0938,	U0936 ] }; // DEVANAGARI LETTER SA; DEVANAGARI LETTER SHA
  key <AB08> { [	comma,		U0937 ] }; // DEVANAGARI LETTER SSA
  key <AB09> { [	period,		U0964 ] }; // DEVANAGARI DANDA
  key <AB10> { [	U092F,	U095F ] }; // DEVANAGARI LETTER YA; DEVANAGARI LETTER YYA

  // space, space, Zero-Width-Non-Joiner (ZWNJ), Zero-Width-Joiner (ZWJ):
  include "nbsp(zwnj3zwj4)"

  include "group(olpc)"
  include "rupeesign(4)"
  include "level3(ralt_switch)"
};

partial alphanumeric_keys
xkb_symbols "hin-wx" {

    name[Group1]= "Hindi (Wx)";

      key <TLDE> {	 [     grave, asciitilde, 2, 3    ]	};

      key <AE01> {	 [      0x1000967, exclam 		]	};
      key <AE02> {	 [      0x1000968, at 		]	};
      key <AE03> {	 [      0x1000969 , numbersign	 		]	};
      key <AE04> {	 [      0x100096A , dollar		]	};
      key <AE05> {	 [      0x100096B , percent 	 		]	};
      key <AE06> {	 [      0x100096C , asciicircum	 		]	};
      key <AE07> {	 [      0x100096D , ampersand                       ]	};
      key <AE08> {	 [      0x100096e , asterisk 	 		]	};
      key <AE09> {	 [      0x100096F, parenleft 		]	};
      key <AE10> {	 [      0x1000966, parenright 		]	};
      key <AE11> {	 [      minus, underscore 	 		]	};
      key <AE12> {	 [      equal, plus 		]	};


      key <AD01> {	 [      0x1000943,  0x1000944, 0x100090B, 0x1000960]	};
      key <AD02> {	 [      0x1000924,  0x1000925       	]	};
      key <AD03> {	 [      0x1000947,  0x1000948, 0x100090F, 0x1000910]	};
      key <AD04> {	 [      0x1000930,  0x1000937       	]	};
      key <AD05> {	 [      0x100091F,  0x1000920       	]	};


      key <AD06> {	 [      0x100092F 		]	};
      key <AD07> {	 [      0x1000941,  0x1000942, 0x1000909, 0x100090A ]	};
      key <AD08> {	 [      0x100093F,  0x1000940, 0x1000907, 0x1000908 ]	};
      key <AD09> {	 [      0x100094B,  0x100094C, 0x1000913, 0x1000914]	};
      key <AD10> {	 [      0x100092A,  0x100092B 		]	};
      key <AD11> {	 [      bracketleft, braceleft  		]	};
      key <AD12> {	 [      bracketright, braceright  		]	};
      key <BKSL> {       [      backslash, bar, 0x1000964, 0x1000965 ] };

      key <AC01> {	 [      0x100094D,  0x100093E, 0x1000905,0x1000906 ] 	};
      key <AC02> {	 [      0x1000938,  0x1000936       	]	};
      key <AC03> {	 [      0x1000921,  0x1000922       	]	};
      key <AC04> {	 [      0x1000919,  0x100091E       	]	};
      key <AC05> {	 [      0x1000917,  0x1000918       	]	};


      key <AC06> {	 [      0x1000939,  0x1000903 		]	};
      key <AC07> {	 [      0x100091C,  0x100091D 		]	};
      key <AC08> {	 [      0x1000915,  0x1000916 		]	};
      key <AC09> {	 [      0x1000932,  0x1000962, 0x1000933, 0x100090C]	};
      key <AC10> {	 [      semicolon, colon  		]	};
      key <AC11> {	 [      apostrophe, quotedbl 		]	};

      key <AB01> {	 [      0x1000901,   0x100093C, 0x100093D, 0x1000950]   };
      key <AB02> {       [      0x1000926,   0x1000927      ]       };
      key <AB03> {       [      0x100091A,   0x100091B         ]       };
      key <AB04> {       [      0x1000935                      ]       };
      key <AB05> {       [      0x100092C,   0x100092D        ]       };
      key <AB06> {       [      0x1000928,   0x1000923         ]       };
      key <AB