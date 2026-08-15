import { APP_INITIALIZER, NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouteReuseStrategy } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';

import { IonicModule, IonicRouteStrategy } from '@ionic/angular';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { authInterceptor } from './core/auth-interceptor';
import { Auth } from './core/auth';

/**
 * Módulo raíz — el único que se carga de entrada (todo lo demás, como
 * LoginPageModule/HomePageModule, se carga perezoso vía rutas). Acá se
 * registran las cosas que aplican a toda la app, una sola vez:
 * - `IonicModule.forRoot()`: inicializa el runtime de Ionic (una sola vez, a diferencia de `IonicModule` a secas que usan los módulos "hijos").
 * - `provideHttpClient(withInterceptors([authInterceptor]))`: habilita `HttpClient` en toda la app y engancha authInterceptor (core/auth-interceptor.ts) para que corra en cada request saliente, sin tener que importarlo en cada módulo feature.
 * - `APP_INITIALIZER` sobre `Auth.inicializar()`: Angular no termina de
 *   bootstrapear (ni arranca el router, ni corre ningún guard) hasta que
 *   esta Promise resuelve — carga los tokens de una sesión anterior desde
 *   `AlmacenamientoSeguro` (async, Keychain/Keystore en nativo) a una copia
 *   en memoria antes de que cualquier `authGuard`/`authInterceptor` pueda
 *   necesitarlos de forma síncrona (ver el comentario largo en `auth.ts`).
 */
@NgModule({
  declarations: [AppComponent],
  imports: [BrowserModule, IonicModule.forRoot(), AppRoutingModule],
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    provideHttpClient(withInterceptors([authInterceptor])),
    {
      provide: APP_INITIALIZER,
      useFactory: (auth: Auth) => () => auth.inicializar(),
      deps: [Auth],
      multi: true,
    },
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
