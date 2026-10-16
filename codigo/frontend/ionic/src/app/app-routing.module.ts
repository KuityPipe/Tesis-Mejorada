import { NgModule, inject } from '@angular/core';
import { PreloadAllModules, Router, RouterModule, Routes } from '@angular/router';

import { authGuard } from './core/auth-guard';

// `loadChildren` con un `import()` dinámico es lazy-loading: el código de
// cada página (y sus dependencias) recién se descarga cuando el usuario
// navega ahí, no en el bundle inicial. `canActivate: [authGuard]` corre el
// guard antes de permitir esa navegación (ver core/auth-guard.ts).
const routes: Routes = [
  {
    path: 'home',
    title: 'Mi cuenta · KeyServ',
    loadChildren: () => import('./home/home.module').then( m => m.HomePageModule),
    canActivate: [authGuard],
  },
  {
    // Landing pública (marketing + búsqueda rápida), equivalente Ionic de
    // `/` (paginicio_view) — distinta de `/catalogo` (listado completo,
    // equivalente de `/servicios/`) y de `/home` (dashboard autenticado,
    // equivalente de `/inicio/`), mismo criterio de 3 rutas separadas que
    // usa el sitio Django.
    path: '',
    loadChildren: () => import('./inicio/inicio.module').then( m => m.InicioPageModule),
  },
  {
    path: 'login',
    title: 'Iniciar sesión · KeyServ',
    loadChildren: () => import('./login/login.module').then( m => m.LoginPageModule)
  },
  {
    path: 'catalogo',
    title: 'Servicios · KeyServ',
    loadChildren: () => import('./catalogo/catalogo.module').then( m => m.CatalogoPageModule)
  },
  {
    // "Acerca de nosotros" vive ahora dentro de la página principal (sección #acerca); la ruta vieja redirige ahí.
    path: 'acerca-de-nosotros',
    redirectTo: () => inject(Router).parseUrl('/#acerca')
  },
  {
    path: 'contacto',
    // Contacto vive al final de la portada (sección #contacto); la ruta vieja redirige ahí.
    redirectTo: () => inject(Router).parseUrl('/#contacto')
  },
  {
    // Política de privacidad (antes solo existía como plantilla de Django, con el diseño y la navegación viejos).
    path: 'privacidad',
    title: 'Política de privacidad · KeyServ',
    loadChildren: () => import('./privacidad/privacidad.module').then( m => m.PrivacidadPageModule)
  },
  {
    path: 'registro',
    title: 'Crear cuenta · KeyServ',
    loadChildren: () => import('./registro/registro.module').then( m => m.RegistroPageModule)
  },
  {
    path: 'perfil/editar',
    title: 'Editar perfil · KeyServ',
    loadChildren: () => import('./perfil/editar/editar.module').then( m => m.EditarPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'perfil/proveedor',
    title: 'Perfil de proveedor · KeyServ',
    loadChildren: () => import('./perfil/proveedor/proveedor.module').then( m => m.ProveedorPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'perfil/publicaciones',
    title: 'Mis publicaciones · KeyServ',
    loadChildren: () => import('./perfil/publicaciones/publicaciones.module').then( m => m.PublicacionesPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'perfil/pagos',
    title: 'Historial de pagos · KeyServ',
    loadChildren: () => import('./perfil/pagos/pagos.module').then( m => m.PagosPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'preferencias',
    title: 'Preferencias de la cuenta · KeyServ',
    loadChildren: () => import('./preferencias/preferencias.module').then( m => m.PreferenciasPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'recuperar',
    title: 'Recuperar contraseña · KeyServ',
    loadChildren: () => import('./recuperar/recuperar.module').then( m => m.RecuperarPageModule)
  },
  {
    path: 'reservas',
    title: 'Mis contrataciones · KeyServ',
    loadChildren: () => import('./reservas/reservas.module').then( m => m.ReservasPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'mensajes',
    title: 'Mensajes · KeyServ',
    loadChildren: () => import('./mensajes/mensajes.module').then( m => m.MensajesPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'contratacion/:id',
    title: 'Detalle del trabajo · KeyServ',
    loadChildren: () => import('./contratacion/detalle/detalle.module').then( m => m.DetallePageModule),
    canActivate: [authGuard],
  },
  {
    // Sin authGuard: Transbank/Khipu redirigen acá directo, y el token JWT
    // de la sesión Ionic puede haber quedado vencido durante el rato que
    // el usuario estuvo fuera de la SPA (ver Pagos.confirmarWebpay/estadoKhipu).
    path: 'pago/webpay/retorno',
    title: 'Resultado del pago · KeyServ',
    loadChildren: () => import('./pago/webpay/retorno/retorno.module').then( m => m.RetornoPageModule),
  },
  {
    path: 'pago/retorno/:metodo/:id',
    title: 'Resultado del pago · KeyServ',
    loadChildren: () => import('./pago/khipu/retorno/retorno.module').then( m => m.RetornoPageModule),
  },
  {
    path: 'pago/khipu/retorno/:id',
    title: 'Resultado del pago · KeyServ',
    loadChildren: () => import('./pago/khipu/retorno/retorno.module').then( m => m.RetornoPageModule),
  },
  {
    path: 'biometria',
    title: 'Verificación biométrica · KeyServ',
    loadChildren: () => import('./biometria/biometria.module').then( m => m.BiometriaPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'verificacion-alternativa',
    title: 'Verificación sin biometría · KeyServ',
    loadChildren: () => import('./verificacion-alternativa/verificacion-alternativa.module').then( m => m.VerificacionAlternativaPageModule),
    canActivate: [authGuard],
  },
  {
    path: 'rostro',
    title: 'Reconocimiento facial · KeyServ',
    loadChildren: () => import('./rostro/rostro.module').then( m => m.RostroPageModule),
    canActivate: [authGuard],
  },
  {
    // Cualquier dirección que no exista: una página que explica y ofrece salidas, en vez de dejar la pantalla en blanco.
    path: '**',
    title: 'Página no encontrada · KeyServ',
    loadChildren: () => import('./no-encontrado/no-encontrado.module').then( m => m.NoEncontradoPageModule),
  },
];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules })
  ],
  exports: [RouterModule]
})
export class AppRoutingModule { }
