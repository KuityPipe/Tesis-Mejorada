import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { FooterComponent } from './footer';

describe('FooterComponent', () => {
  let component: FooterComponent;
  let fixture: ComponentFixture<FooterComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [FooterComponent],
      imports: [RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(FooterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('muestra el año actual en el copyright', () => {
    expect(component.anioActual).toBe(new Date().getFullYear());
  });

  it('enlaza la política de privacidad dentro de la app, no al sitio de Django', () => {
    const enlace: HTMLAnchorElement = fixture.nativeElement.querySelector('a[href="/privacidad"]');
    expect(enlace).toBeTruthy();
    expect(enlace.target).not.toBe('_blank');
  });
});
