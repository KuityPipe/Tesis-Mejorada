import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { ProveedorPage } from './proveedor.page';
import { SharedModule } from '../../shared/shared.module';

describe('ProveedorPage', () => {
  let component: ProveedorPage;
  let fixture: ComponentFixture<ProveedorPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ProveedorPage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(ProveedorPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
