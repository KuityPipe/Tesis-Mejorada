import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { ConfirmarPage } from './confirmar.page';

describe('ConfirmarPage', () => {
  let component: ConfirmarPage;
  let fixture: ComponentFixture<ConfirmarPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ConfirmarPage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule],
    }).compileComponents();

    fixture = TestBed.createComponent(ConfirmarPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
