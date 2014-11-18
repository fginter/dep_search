#ifndef __query_functions_h__
#define __query_functions_h__

#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <stddef.h>
#include "setlib/tset.h"

void pairing(tset::TSet *index_set, tset::TSet *other_set, tset::TSetArray *mapping, bool negated);


#endif
