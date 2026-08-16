import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { IonicModule } from '@ionic/angular';

import { EditarPage } from './editar.page';
import { SharedModule } from '../../shared/shared.module';

describe('EditarPage', () => {
  let component: EditarPage;
  let fixture: ComponentFixture<EditarPage>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [EditarPage],
      imports: [IonicModule.forRoot(), ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule, SharedModule],
    }).compileComponents();

    fixture = TestBed.createComponent(EditarPage);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
