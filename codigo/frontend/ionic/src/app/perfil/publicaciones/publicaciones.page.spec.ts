import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { PublicacionesPage } from './publicaciones.page';
import { SharedModule } from '../../shared/shared.module';

describe('PublicacionesPage', () => {
  let component: PublicacionesPage;
  let fixture: ComponentFixture<PublicacionesPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PublicacionesPage],
      imports: [IonicModule.forRoot(), HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(PublicacionesPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
