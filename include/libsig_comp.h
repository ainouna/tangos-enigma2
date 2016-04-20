#ifndef __LIBSIG_COMP_H
#define __LIBSIG_COMP_H

#include <sigc++/sigc++.h>
#include <sigc++/bind.h>

#ifdef SIGC_CXX_NAMESPACES
using namespace SigC;
#endif

#ifdef ENABLE_SIGC2

typedef sigc::trackable  Object;
typedef sigc::connection Connection;

#define Signal0          sigc::signal0
#define Signal1          sigc::signal1
#define Signal2          sigc::signal2
#define Signal3          sigc::signal3
#define Signal4          sigc::signal4

#define Slot0            sigc::slot0
#define Slot1            sigc::slot1
#define Slot2            sigc::slot2

#define slot(x, y)       sigc::mem_fun(x, y)

#define CONNECT(SENDER, EMPFAENGER) SENDER.connect(sigc::mem_fun(*this, &EMPFAENGER))
#else
#define CONNECT(SENDER, EMPFAENGER) SENDER.connect(slot(*this, &EMPFAENGER))
// use this Makro to connect with a method
// void bla::foo(int x);
// to an
// Signal<void, int> testSig;
//
// CONNECT(testSig, bla::foo);
// signal and method (slot) must have the same signature
#endif //SIGC2

#define CONNECT_1_0(SENDER, EMPFAENGER, PARAM) SENDER.connect( bind( slot(*this, &EMPFAENGER) ,PARAM ) )
// use this for connect with a method
// void bla::foo(int);
// to an
// Signal0<void> testSig;
// CONNECT_1_0(testSig, bla:foo, 0);
// here the signal has no parameter, but the slot have an int
// the last parameter of the CONNECT_1_0 makro is the value that given to the paramater of the Slot method

#define CONNECT_2_0(SENDER, EMPFAENGER, PARAM1, PARAM2) SENDER.connect( bind( slot(*this, &EMPFAENGER) ,PARAM1, PARAM2 ) )

#define CONNECT_2_1(SENDER, EMPFAENGER, PARAM) SENDER.connect( bind( slot(*this, &EMPFAENGER) ,PARAM ) )

#endif // __LIBSIG_COMP_H
