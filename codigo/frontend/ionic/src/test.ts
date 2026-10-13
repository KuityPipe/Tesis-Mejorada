// This file is required by karma.conf.js and loads recursively all the .spec and framework files

import 'zone.js/testing';
import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing';

// First, initialize the Angular testing environment.
getTestBed().initTestEnvironment(
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting(),
);

// Carrera conocida de Ionic en pruebas: un `ion-input`/`ion-select` ya destruido recibe un último callback de aria
// (`onAriaChanged`) y lanza un error no capturado que Jasmine le atribuye a la prueba que esté corriendo. No es un
// fallo de la app: se filtra ese único error, el resto sigue llegando a Jasmine.
declare const jasmine: any;
jasmine.getEnv().beforeAll(() => {
  const previo = window.onerror;
  window.onerror = (mensaje, ...resto) => {
    if (String(mensaje).includes('onAriaChanged')) {
      return true;
    }
    return previo ? (previo as any)(mensaje, ...resto) : false;
  };
});
