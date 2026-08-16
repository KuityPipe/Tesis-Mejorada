import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { PreferenciasPage } from './preferencias.page';
import { SharedModule } from '../shared/shared.module';

describe('PreferenciasPage', () => {
  let component: PreferenciasPage;
  let fixture: ComponentFixture<PreferenciasPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [PreferenciasPage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(PreferenciasPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
